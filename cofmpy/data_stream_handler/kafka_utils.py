# -*- coding: utf-8 -*-
# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
# The 2-Clause BSD License
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Helper classes handling Kafka configuration, Threads, messages, etc
"""
import logging
import threading
import time
from dataclasses import dataclass, field

from ..utils import Interpolator


logger = logging.getLogger(__name__)


@dataclass
class KafkaHandlerConfig:  # pylint: disable=too-many-instance-attributes
    """
    Configuration handler for Kafka connections.

    This dataclass manages Kafka connection parameters, providing default values
    for optional arguments and enforcing required fields. It automatically
    splits the `uri` into `server_url` and `port`, and validates field types
    and allowed values after initialization (i.e. after applying default values).

    Attributes:
        topic (str): Kafka topic to subscribe/publish to. Required.
        uri (str): Connection URI in the format "server_url:port". Required.
        variable (str): Name of the variable associated with the Kafka stream. Required.
        group_id (str): Kafka consumer group ID. Required.
        server_url (str): Extracted server URL from `uri`. Initialized post-init.
        port (str): Extracted port from `uri`. Initialized post-init.
        timeout (float): Timeout in seconds for Kafka operations. Defaults to 0.1.
        interpolation (str): Method used for data interpolation. Defaults to "previous".
        auto_offset_reset (str): Offset reset strategy for Kafka consumer. Defaults to "earliest".
            Allowed values: "earliest", "latest", "none".
        enable_auto_commit (bool): Whether to automatically commit offsets. Defaults to True.

    Raises:
        ValueError: If `uri` is malformed, `port` is not numeric, `timeout` is negative,
                    `auto_offset_reset` is invalid, or `interpolation` is not supported.
    """

    # Required fields
    topic: str
    uri: str
    group_id: str

    # Split fields, initialized in __post_init__
    server_url: str = field(init=False)
    port: str = field(init=False)

    # Optional fields with defaults
    timeout: float = 0.1
    interpolation: str = "previous"
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True
    first_msg_timeout: float = 35
    max_retries: int = 3
    retry_delay: float = 0.02
    first_delay: float = 4
    thread_lifetime: float = 3600
    backend_conf_path: str = ""
    offset_reset: str = "earliest"
    max_buffer_len: int = 10

    def __post_init__(self):

        # Split URI
        try:
            self.server_url, self.port = self.uri.split(":")
        except ValueError as exc:
            raise ValueError(f"Malformed URI in Kafka config: {self.uri!r}") from exc

        # ----- Argument validations -----

        if not self.port.isdigit():
            raise ValueError(f"Port must be numeric, got '{self.port}'")

        if self.timeout < 0:
            raise ValueError(f"Timeout must be non-negative, got {self.timeout}")

        valid_offsets = {"earliest", "latest", "none"}
        if self.auto_offset_reset not in valid_offsets:
            raise ValueError(
                "Invalid auto_offset_reset: "
                f"'{self.auto_offset_reset}'. Must be one of {valid_offsets}"
            )

        valid_interpolation = getattr(Interpolator, "_registry", {}).keys()
        if self.interpolation not in valid_interpolation:
            raise ValueError(
                "Invalid interpolation method: "
                f"'{self.interpolation}'. Must be one of {list(valid_interpolation)}"
            )


class KafkaThreadManager:
    """
    Manages a background thread to consume messages from a Kafka topic.

    This class wraps a Kafka consumer (e.g., from `confluent_kafka`) and runs
    a separate thread to continuously poll messages. Incoming messages are
    processed using a callback function provided by the user. The thread can
    run for a limited lifetime or indefinitely.

    Attributes:
        consumer: A Kafka consumer object that handles message fetching.
        callback: A function that is called for each message received.
        thread_lifetime (float): Maximum lifetime of the thread in seconds.
            If None or 0, the thread runs indefinitely.
        running (bool): Flag indicating whether the consuming thread is active.
        thread (threading.Thread): The background thread running the consume loop.
        start_time (float): Timestamp when the thread started, used to track lifetime.

    Methods:
        start(): Start the consuming thread.
        stop(): Gracefully stop the consuming thread.
        _consume_loop(): Internal method running the main polling loop.

    Example:
        def process_message(msg):
            print("Received message:", msg.value())

        manager = KafkaThreadManager(
            consumer=my_consumer,
            callback=process_message,
            thread_lifetime=60
        )
        manager.start()
        # ... do other work ...
        manager.stop()
    """

    def __init__(self, consumer, callback, thread_lifetime=40):
        """Constructor requires the confluent_kafka consumer object
        and on_consume callback

        Args:
            consumer (confluent_kafka.Consumer): consumer object
            callback (function): on_consume callback
        """
        self.consumer = consumer
        self.callback = callback
        self.thread_lifetime = thread_lifetime
        self.running = False
        self.thread = None
        self.start_time = None

    def start(self):
        """
        Start the Kafka consuming thread.

        This method creates and starts a background thread that continuously polls
        messages from the Kafka consumer. If a thread lifetime was specified during
        initialization, the thread will automatically stop after that duration.

        Sets `self.running` to True and initializes `self.start_time`.

        Logs the start of the thread.
        """
        if self.thread_lifetime:
            self.start_time = time.time()
        if not self.running:
            self.running = True
            # Create a background thread to run the consume loop
            self.thread = threading.Thread(target=self._consume_loop)
            # Make it a daemon so it stops with the main program
            self.thread.daemon = True
            self.thread.start()
            logger.info(
                f"Kafka consumer started consuming in thread '{self.thread.name}'"
            )

    def _consume_loop(self):
        """
        Main polling loop that runs inside the background thread.

        Continuously polls messages from the Kafka consumer while `self.running` is True.
        Each received message is passed to the user-provided callback function.

        If a thread lifetime was specified, the loop stops when the elapsed time
        exceeds `thread_lifetime`. Any polling errors are logged but do not stop the loop.

        After exiting the loop, the consumer is closed and `self.running` is set to False.

        Note:
            This method is intended to run inside a background thread and should
            not be called directly from the main program.

        Example:
            # Internal use only:
            threading.Thread(target=manager._consume_loop).start()
        """
        msg = None
        while self.running:
            elapsed = time.time() - self.start_time
            if elapsed > self.thread_lifetime:
                logger.info("Thread lifetime reached. Stopping thread.")
                self.running = False
                break

            try:
                msg = self.consumer.poll(timeout=1)
                if not msg:
                    continue  # Skip processing for empty messages

            except Exception as e:
                logger.error(f"Consumer error when polling message: {e}")

            else:
                # Callback should implement error handling
                self.callback(msg)

        logger.info("'running' set to False, closing consumer.")
        self.consumer.close()

    def stop(self):
        """Gracefully stop the Kafka consuming thread.

        This method sets the `self.running` flag to False, which signals the
        background thread to exit its polling loop. It then waits for the thread
        to finish by calling `join()`.

        After this method is called, the Kafka consumer is closed and no further
        messages will be processed.
        """
        if self.running:
            self.running = False
            self.thread.join()
            logger.info("Kafka consumer thread stopped.")
