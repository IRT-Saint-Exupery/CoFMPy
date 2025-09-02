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

    def __init__(self, topic, uri, group_id, variable, **kwargs):
        """
        Constructor for Kafka data stream handler.

        Args:
            kwargs: kafka service configuration.
        """

        # Configuration handling
        positional = {
            "topic": topic,
            "uri": uri,
            "group_id": group_id,
            "variable": variable,
        }
        kwargs.update(positional)
        self.config = KafkaHandlerConfig.from_dict(kwargs)
        logger.debug(f"Parsed config for {self}: {vars(self.config)}")

        # Data-related instances
        self.interpolator = Interpolator(self.config.interpolation)
        self.data = pd.DataFrame(columns=["t", self.config.variable])

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
            "group.id": f"{self.config.group_id}_{self.config.variable}",
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

    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            dict: data at the requested time: {'var1': val1 , ...}.
        """
        self._lazy_subscribe()

        while True:

            try:
                data = self.data.copy()

                if data.shape[0] == 0:
                    time.sleep(0.01)
                    continue

                # Data has started arriving
                # Apply timeout only once (data should arrive at once)
                if self.config.timeout >= 0:
                    logging.debug(
                        "First data recovered ('get_data')'. "
                        f"Shape: {data.shape}. "
                        f"Will wait {self.config.timeout} sec before proceeding."
                    )

                    # Wait and update data after timeout
                    time.sleep(self.config.timeout)
                    data = self.data.copy()

                    self.config.timeout = -1

                x_p = data["t"]
                # x_p = data.index
                y_p = data[self.config.variable]

                return self.interpolator(x_p, y_p, [t])

            except (AttributeError, KeyError, ValueError) as error:
                logger.error(f"Error: {error}")

            time.sleep(0.05)

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
        """Process an individual Kafka message."""
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
