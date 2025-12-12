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
This module contains the child class for Kafka data stream handler.
"""
import json
import logging
import threading
import time

import pandas as pd
from confluent_kafka import Consumer
from confluent_kafka import KafkaError
from confluent_kafka import KafkaException

from ..utils import Interpolator
from .base_data_stream_handler import BaseDataStreamHandler
from .kafka_utils import KafkaHandlerConfig
from .kafka_utils import KafkaThreadManager

logger = logging.getLogger(__name__)


class KafkaDataStreamHandler(BaseDataStreamHandler):
    """Child class for Kafka data stream handler."""

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "kafka"

    def __init__(self, topic, uri, group_id, **kwargs):
        """
        Constructor for Kafka data stream handler.

        Args:
            kwargs: kafka service configuration.
        """
        super().__init__()

        # Configuration handling
        positional = {"topic": topic, "uri": uri, "group_id": group_id}
        kwargs.update(positional)
        self.config = KafkaHandlerConfig(**kwargs)
        logger.debug(f"Parsed config for {self}: {vars(self.config)}")

        # Data-related instances
        self.interpolator = Interpolator(self.config.interpolation)
        self.data = pd.DataFrame(columns=["t"])

        self._data_lock = threading.Lock()
        self._subscribed = False
        self.first_received = None
        self.consumer = self._create_consumer()

        self.thread_manager = KafkaThreadManager(self.consumer, self._handle_message)
        self.start_consumer_thread()

    def _create_consumer(self):
        """Creates and configures a Kafka consumer

        Returns:
            confluent_kafka.Consumer: Consumer instance
        """
        kafka_config = {
            "bootstrap.servers": f"{self.config.server_url}:{self.config.port}",
            "group.id": self.config.group_id,
            "enable.auto.commit": self.config.enable_auto_commit,
            "auto.offset.reset": self.config.auto_offset_reset,
        }
        logger.debug(f"Creating Kafka consumer with config: {kafka_config}")
        consumer = Consumer(kafka_config)
        logger.debug("Kafka consumer created successfully.")
        return consumer

    def _lazy_subscribe(self):
        """One-time subscription"""
        if not self._subscribed:
            self.consumer.subscribe([self.config.topic])
            self._subscribed = True

    def _build_out_dict(self, t_s):
        """Builds the requested dictionary (output of get_data). Iterates over alias_mapping
        to get variable names or alias. Uses interpolator to retrieve data at requested time
        from self.data (pd.DataFrame).

        Args:
            ts (float): requested timestamp

        Returns:
            dict[tuple:float]: requested float values per variable (tuple key)
        """
        out_dict = {}
        for (fmu, variable), var_name in self.alias_mapping.items():
            out_dict[(fmu, variable)] = self.interpolator(
                self.data["t"], self.data[var_name], [t_s]
            )[0]

        return out_dict

    def get_data(self, t: float):
        """
        Retrieve data corresponding to a specific timestamp, with optional interpolation.

        This method waits for the required data to become available in a thread-safe way.
        It distinguishes between the first data retrieval (allowing a longer timeout to
        handle sparse data sources) and subsequent retrievals with a shorter retry window.

        Args:
            t (float): The target timestamp for which data is requested.

        Returns:
            dict or None:
                - A list containing the interpolated or exact data. Format: [float]
                - Returns None if data could not be retrieved within the configured timeouts.

        Notes:
            - If the consumer thread is not running, an error is logged and None is returned.
            - The first message is awaited with a longer timeout to better handle sparse
                data sources.
        """
        logger.debug(f"Getting data for timestamp: {t}")

        if not self.thread_manager.running:
            logger.error("Consumer thread is not running. Cannot get data.")
            return None

        self._lazy_subscribe()

        with self._data_lock:
            data_len = len(self.data)
            logger.debug(f"Current data buffer size: {data_len}")

        # First-time handling with extended timeout
        if data_len == 0:
            logger.info(
                "Waiting for first Kafka message "
                f"(timeout = {self.config.first_msg_timeout})"
            )
            start_time = time.time()
            while time.time() - start_time < self.config.first_msg_timeout:
                try:
                    with self._data_lock:
                        logger.debug(
                            "1st msg attempt: trying to fetch data. "
                            f"Available t_series: {self.data['t']}. "
                            f"Requested ts: {t}"
                        )
                        return self._build_out_dict(t)
                except KeyError as error:
                    logger.error(f"Missing key: {error}")
                except (ValueError, RuntimeError) as error:
                    logger.error(f"{type(error).__name__}: {error}")
                time.sleep(self.config.retry_delay)

        # Regular retry loop for existing streams
        for _ in range(self.config.max_retries):
            start_time = time.time()
            while time.time() - start_time < self.config.timeout:
                with self._data_lock:
                    logger.debug(f"Fetching data for ts = {t}")
                    return self._build_out_dict(t)
            logger.error(f"No valid data for ts = {t} after retries.")

        return None

    def send_data(self, data):
        """
        Send data to the Kafka topic.

        Args:
            data (str): data to send.
        """
        self.consumer.produce(self.config.topic, value=data)
        self.consumer.poll(0)
        self.consumer.flush()
        logger.info(f"Data sent to Kafka topic {self.config.topic}.")

    @staticmethod
    def parse_kafka_message(msg: str):
        """Method for parsing Kafka consumed messages.

        Args:
            msg (str): message.

        Returns:
            dict: data dictionary: {"t": t, "var":var}.
        """

        # Get/decode/format messsage
        msg = msg.value().decode("utf-8").replace("'", '"')

        # Parse message: str -> dict
        msg = json.loads(msg)

        # Structure message
        msg = {k: [float(v)] for k, v in msg.items()}

        row = pd.DataFrame(msg)  # .set_index("t")

        return row

    def _handle_message(self, message):
        """
        Process a single Kafka message (typically used as callback
        for KafkaThreadManager).

        * If the message has an error, log an end-of-partition warning or raise
        `kafka.KafkaException` for other errors.
        * Otherwise parse the payload, merge it into `self.data`
        (dropping duplicates), and mark the first successful message.
        * All `AttributeError`, `KeyError`, or
        `ValueError` raised during processing are logged and ignored.

        Parameters
        ----------
        message : confluent_kafka.Message
            A message returned by the consumer.

        Notes
        -----
        * `self.first_received` is set only once, after the first
        successfully parsed message.
        * `self.data` is updated with new rows and reset-indexed; empty
        frames are ignored.
        """
        try:
            if message.error():
                if message.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition reached
                    err = f"End of partition: {message.partition} offset: {message.offset}"
                    logger.error(err)
                else:
                    raise KafkaException(message.error())
            else:
                # parse message
                last_data = self.parse_kafka_message(message)

                frames = [df for df in [self.data, last_data] if not df.empty]

                if frames:
                    self.data = (
                        pd.concat(frames).drop_duplicates().reset_index(drop=True)
                    )

                if self.first_received is None:
                    logger.info(
                        f"First message consumed: "
                        f"{message.value().decode('utf-8')}"
                        f"(offset: {message.offset()})"
                    )
                    self.first_received = message
        except (AttributeError, KeyError, ValueError) as error:
            logger.error(f"Error handling messages: {error}")

    def start_consumer_thread(self):
        """Start the consumer in a background thread."""
        logger.debug("Starting Kafka consumer thread.")
        self.thread_manager.start()

    def stop_consumer_thread(self):
        """Stop the consumer gracefully."""
        logger.debug("Stopping Kafka consumer thread.")
        self.thread_manager.stop()

    # pylint: disable=W0237,W0221
    def is_equivalent_stream(self, topic, uri, group_id, **alt_config) -> bool:
        """
        Check if the current data stream handler instance is equivalent to
        another that would be created with the given config.
        This kafka data handler groups all variables sent in the same
        {uri, topic, group} data stream into one handler instance.

        Args:
            The constructor is exacly the same than in __init__.

        Returns:
            bool: True if the handlers are equivalent, False otherwise.
        """
        # equivalent items: {uri, topic, group_id, interpolation}
        # if one is different, the compared streams are not equivalent
        interp_method = alt_config.get("interpolation", "previous")
        same = (
            f"{self.config.server_url}:{self.config.port}" == uri
            and self.config.topic == topic
            and self.config.group_id == group_id
            and self.config.interpolation == interp_method
        )
        logger.debug("Stream equivalence check: %s", same)
        return same
