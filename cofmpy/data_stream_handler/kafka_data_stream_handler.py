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
This module contains the child class for Kafka data stream handler.
"""

import time
import logging
import threading

from confluent_kafka import Consumer, KafkaError, KafkaException
from sortedcontainers import SortedDict

from ..utils import Interpolator, lookup_with_window
from .base_data_stream_handler import BaseDataStreamHandler
from .kafka_utils import KafkaHandlerConfig, KafkaThreadManager, parse_kafka_message

logger = logging.getLogger(__name__)


class KafkaDataStreamHandler(BaseDataStreamHandler):
    """Child class for Kafka data stream handler."""

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "kafka"

    def __init__(self, config):
        """
        Constructor for Kafka data stream handler.

        Args:
            kwargs: kafka service configuration.
        """
        super().__init__()
        logger.debug("Initializing KafkaDataStreamHandler with config: %s", config)

        self._first_msg = None
        self._subscribed = False
        self._warned = False
        self._data_lock = threading.Lock()
        self.config = KafkaHandlerConfig.from_dict(config)
        logger.debug("Parsed KafkaHandlerConfig: %s", vars(self.config))

        self.interpolator = Interpolator(self.config.interpolation)
        logger.debug(
            "Initializing Interpolator with method: %s", self.interpolator.method
        )
        self.consumer = self._create_consumer()
        self.thread_manager = KafkaThreadManager(
            self.consumer, self._handle_message, self.config.thread_lifetime
        )
        self.data = SortedDict()

        self.start_consumer()
        logger.debug("Kafka consumer thread started.")

    def _create_consumer(self):
        """Creates and configures a confluent_kafka consumer

        Returns:
            confluent_kafka.Consumer: Consumer instance
        """
        kafka_config = {
            "bootstrap.servers": f"{self.config.server_url}:{self.config.port}",
            "group.id": self.config.group_id,
            "enable.auto.commit": True,
            "auto.offset.reset": self.config.offset_reset,
        }
        logger.debug("Creating Kafka consumer with config: %s", kafka_config)

        consumer = Consumer(kafka_config)
        time.sleep(0.05)
        logger.debug("Kafka consumer created successfully.")
        return consumer

    def _lazy_subscribe(self):
        """One-time subscription"""
        if not self._subscribed:
            logger.debug("Subscribing to Kafka topic: %s", self.config.topic)
            self.consumer.subscribe([self.config.topic])
            self._subscribed = True
            logger.info(
                "Kafka subscription completed for topic '%s'.", self.config.topic
            )

    def _handle_message(self, message):
        """Handles kafka exceptions given a single message

        Args:
            message (bytes): kafka message

        Raises:
            KafkaException: kafka error different than end-of-partition
        """
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                logger.warning(
                    "Partition EOF: partition %s, offset %s",
                    message.partition(),
                    message.offset(),
                )
            else:
                logger.error("Kafka error occurred: %s", message.error())
                raise KafkaException(message.error())
            return

        logger.debug("Received Kafka message: %s", message.value())
        message = parse_kafka_message(message)
        logger.debug("Parsed Kafka message: %s", message)

        with self._data_lock:
            # Actual writing of message into self.data
            self.data[message["t"]] = message
            if self._first_msg is None:
                self._first_msg = message
                logger.info("First Kafka message stored at timestamp: %s", message["t"])
                logger.info("self.data: %s", self.data)

    def _build_out_dict(self, ts_list, val_list, ts):
        """Builds the requested dictionary (output of get_data) by using the interpolator
        on each variable. Uses alias_mapping to build the output tuple-key dictionary from
        the alias one.

        Args:
            ts_list (list[float]): list of timestamps
            val_list (list[dict[str:float]]): list of dicts. Each dict contains a float
                value for each variable (corresponding to the alias key).
            ts (float): requested timestamp

        Returns:
            dict[tuple:float]: requested float values per variable (tuple key)
        """
        out_dict = {}
        for (node, endpoint), alias in self.alias_mapping.items():
            out_dict[(node, endpoint)] = self.interpolator(
                ts_list, [va[alias] for va in val_list], [ts]
            )[0]

        return out_dict

    def get_data(self, t: float):
        """
        Retrieve data corresponding to a specific timestamp, with optional interpolation.

        This method waits for the required data to become available in a thread-safe way.
        It distinguishes between the first data retrieval (allowing a longer timeout to
        handle sparse data sources) and subsequent retrievals with a shorter retry window.

        If interpolation is required (depending on configuration), sufficient past and
        future data points must be available. The method will retry fetching the data
        several times before giving up.

        Args:
            t (float): The target timestamp for which data is requested.

        Returns:
            dict or None:
                - A dictionary containing the interpolated or exact data in the format:
                [value_i:float]
                - Returns None if data could not be retrieved within the configured timeouts.

        Notes:
            - If the consumer thread is not running, an error is logged and None is returned.
            - The first message is awaited with a longer timeout to better handle sparse
                data sources.
        """
        if not self.thread_manager.running:
            logger.error("Consumer thread is not running. Cannot get data.")
            return None

        self._lazy_subscribe()
        logger.debug("Getting data for timestamp: %f", t)

        # Determine required points based on interpolation strategy
        min_pts = (
            0
            if self.config.interpolation == "previous"
            else self.interpolator._min_points[self.interpolator.method]
        )
        logger.debug("Interpolation requires at least %d points", min_pts)

        # Longer timeout for the first message to handle sparse data sources.
        # Can be improved for better flexibility.
        with self._data_lock:
            data_len = len(self.data)
        logger.debug("Current data buffer size: %d", data_len)

        # First-time handling with extended timeout
        if data_len == 0:
            logger.info(
                "Waiting for first Kafka message (timeout = %f)",
                self.config.first_msg_timeout,
            )
            start_time = time.time()
            while time.time() - start_time < self.config.first_msg_timeout:
                with self._data_lock:
                    status, ts_list, val_list = lookup_with_window(
                        self.data, t, min_pts
                    )
                if status:
                    logger.debug(
                        "Successfully executed lookup on %s,%s, %s",
                        self.data,
                        t,
                        min_pts,
                    )
                    logger.debug(
                        "Lookup returned: %s,%s, %s", status, ts_list, val_list
                    )
                    logger.debug("Found interpolation window for ts %f: %s", t, ts_list)
                    time.sleep(self.config.first_delay)
                    out_dict = self._build_out_dict(ts_list, val_list, t)
                    logger.debug(
                        "Returning interpolated data for ts %f: %s", t, out_dict
                    )
                    return out_dict
                time.sleep(self.config.retry_delay)
            logger.warning("Timeout exceeded while waiting for first message.")
            return None  # First-time timeout exceeded

        # Regular retry loop for existing streams
        for _ in range(self.config.max_retries):
            start_time = time.time()
            while time.time() - start_time < self.config.timeout:
                with self._data_lock:
                    status, ts_list, val_list = lookup_with_window(
                        self.data, t, min_pts
                    )
                if status:
                    out_dict = self._build_out_dict(ts_list, val_list, t)
                    return out_dict
                time.sleep(self.config.retry_delay)

        logger.warning("No valid data found for timestamp %f after retries.", t)
        return None

    def send_data(self, data):
        """
        Send data to the Kafka topic.

        Args:
            data (str): data to send.
        """
        logger.warning("send_data has not been tested")
        self.consumer.produce(self.config.topic, value=data)
        self.consumer.poll(0)
        self.consumer.flush()
        logger.info("Data sent to Kafka topic '%s'.", self.config.topic)

    def is_equivalent_stream(self, config: dict) -> bool:
        """
        Check if the current data stream handler instance is equivalent to
        another that would be created with the given config.
        This kafka data handler groups all variables sent in the same
        {uri, topic, group} data stream into one handler instance.

        Args:
            config (dict): config for the data stream handler to compare.

        Returns:
            bool: True if the handlers are equivalent, False otherwise.
        """
        # equivalent items: {uri, topic, group_id}
        uri = f"{self.config.server_url}:{self.config.port}"
        topic = self.config.topic
        group_id = self.config.group_id

        same = (
            config["config"]["uri"] == uri
            and config["config"]["topic"] == topic
            and config["config"]["group_id"] == group_id
        )
        logger.debug("Stream equivalence check: %s", same)
        return same

    def start_consumer(self):
        """Start/restart consumer thread"""
        logger.debug("Starting Kafka consumer thread.")
        self.thread_manager.start()

    def stop_consumer(self):
        """Gracefully stop consumer thread"""
        logger.debug("Stopping Kafka consumer thread.")
        self.thread_manager.stop()
