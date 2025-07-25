# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
"""
Helper classes handling Kafka configuration, Threads, messages, etc
"""

from pathlib import Path
import time
import threading
import logging
import json
from typing import Union

import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KafkaHandlerConfig:  # pylint: disable=too-many-instance-attributes
    """
    Handler to configure Kafka connections.
    """

    # Positional arguments
    topic: str
    variable: str
    server_url: str
    port: str
    group_id: str

    # Optional arguments with defaults
    kafka_backend_conf: str = ""
    timeout: float = 0.1
    first_msg_timeout: float = 35
    max_retries: int = 3
    retry_delay: float = 0.02
    first_delay: float = 4
    interpolation: str = "previous"
    offset_reset: str = "earliest"
    max_buffer_len: int = 10
    thread_lifetime: float = np.inf

    @classmethod
    def from_dict(cls, config: dict):
        """Builds up the configuration Dataclass

        Args:
            config (dict): kwargs-like dictionary

        Returns:
            dataclass: class storing config data
        """

        uri_split = config["uri"].split(":")

        kafka_backend_conf = config.get("kafka_backend_conf", "")
        kafka_backend_path = Path(kafka_backend_conf)

        if kafka_backend_conf and kafka_backend_path.exists():
            with kafka_backend_path.open(encoding="utf-8") as f:
                backend_data = json.load(f)
                config.update(backend_data)

        return cls(
            topic=config["topic"],
            variable=config["variable"],
            server_url=uri_split[0],
            port=uri_split[1],
            group_id=config["group_id"],
            first_msg_timeout=config.get("first_msg_timeout", cls.first_msg_timeout),
            timeout=config.get("timeout", cls.timeout),
            max_retries=config.get("max_retries", cls.max_retries),
            retry_delay=config.get("retry_delay", cls.retry_delay),
            first_delay=config.get("first_delay", cls.first_delay),
            interpolation=config.get("interpolation", cls.interpolation),
            offset_reset=config.get("offset_reset", cls.offset_reset),
            max_buffer_len=config.get("max_buffer_len", cls.max_buffer_len),
            thread_lifetime=config.get("thread_lifetime", cls.thread_lifetime),
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


def parse_kafka_message(msg) -> Union[dict, str]:
    """Parses a single Kafka message and returns it in the desired format.

    Args:
        msg: Kafka message object with a .value() method returning bytes.

    Returns:
        Union[dict, str]: Parsed message as dict, or raw string if parsing fails.
    """

    raw = msg.value().decode("utf-8", errors="replace")

    try:
        # Assume dict-like structure
        data = json.loads(raw.replace("'", '"'))

        if not isinstance(data, dict):
            logger.error("Parsed message is not a dictionary.")
            return data

        return data

    except Exception as e:
        logger.error(f"Failed to parse message ({raw}) due to: {e}")
        return raw
