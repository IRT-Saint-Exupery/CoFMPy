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
from dataclasses import dataclass
from typing import Any
from typing import Dict

from ..utils import Interpolator


logger = logging.getLogger(__name__)


@dataclass
class KafkaHandlerConfig:  # pylint: disable=too-many-instance-attributes
    """
    Handler to configure Kafka connections, providing default values.
    """

    # Positional arguments
    topic: str
    server_url: str
    port: str
    group_id: str
    variable: str

    # Optional arguments from config.json
    timeout: float = 0.1
    interpolation: str = "previous"
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = True

    def __post_init__(self):

        if not self.port.isdigit():
            raise ValueError(f"Port must be numeric, got '{self.port}'")

        if self.timeout < 0:
            raise ValueError(f"Timeout must be non-negative, got {self.timeout}")

        valid_offsets = {"earliest", "latest", "none"}
        if self.auto_offset_reset not in valid_offsets:
            raise ValueError(
                f"Invalid auto_offset_reset: '{self.auto_offset_reset}'. "
                f"Must be one of {valid_offsets}"
            )

        interpolator = Interpolator()
        valid_interpolation = set(interpolator._registry.keys())
        if self.interpolation not in valid_interpolation:
            raise ValueError(
                f"Invalid interpolation method: '{self.interpolation}'. "
                f"Must be one of {valid_interpolation}"
            )

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "KafkaHandlerConfig":
        """Builds up the configuration Dataclass

        Args:
            config (dict): kwargs-like dictionary

        Returns:
            dataclass: class storing config data
        """

        required = {"uri", "topic", "variable", "group_id"}
        missing = required - set(config.keys())
        if missing:
            for key in missing:
                logger.error(f"Missing kafka config field: {key}")
            raise KeyError("Configuration for KafkaDataStreamHandler is incomplete")

        try:
            server_url, port = config["uri"].split(":")
        except ValueError as exc:
            raise ValueError(
                f"Malformed URI in Kafka config: {config['uri']!r}"
            ) from exc

        return cls(
            topic=config["topic"],
            variable=config["variable"],
            server_url=server_url,
            port=port,
            group_id=config["group_id"],
            timeout=config.get("timeout", cls.timeout),
            interpolation=config.get("interpolation", cls.interpolation),
            auto_offset_reset=config.get("auto_offset_reset", cls.auto_offset_reset),
            enable_auto_commit=config.get("enable_auto_commit", cls.enable_auto_commit),
        )


class KafkaThreadManager:
    """Class managing the thread for the kafka consumer"""

    def __init__(self, consumer, callback, thread_lifetime=40):
        """Constructor requires the confluent_kafka consumer object
        and on_consume callback

        Args:
            consumer (_type_): _description_
            callback (function): _description_
        """
        self.consumer = consumer
        self.callback = callback
        self.thread_lifetime = thread_lifetime
        self.running = False
        self.thread = None
        self.start_time = None

    def start(self):
        """Start consuming thread"""
        if self.thread_lifetime:
            self.start_time = time.time()
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._consume_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info(
                f"Kafka consumer started consuming in thread '{self.thread.name}'"
            )

    def _consume_loop(self):
        """Consuming loop."""
        full_counter = 0
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
                    continue

                self.callback(msg)
                full_counter += 1

            except Exception as e:
                logger.error(f"Error consuming messages: {e}")
        logger.info("'running' set to False, closing consumer.")
        self.consumer.close()

    def stop(self):
        """Gracefully stop the consuming thread"""
        if self.running:
            self.running = False
            self.thread.join()
            logger.info("Kafka consumer thread stopped.")
