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
import json
import threading
import logging

import pandas as pd
from confluent_kafka import Consumer, KafkaError, KafkaException

from ..utils import Interpolator
from .base_data_stream_handler import BaseDataStreamHandler

logging.basicConfig(level=logging.INFO)
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
        interp_method, self.timeout = self._validate_config(kwargs)
        self.topic = topic
        server_url, port = uri.split(":")
        self.group_id = group_id
        self.var_name = variable

        # Consumer isntantiation
        self._start_consumer(server_url, port, group_id)
        self._subscribed = False

        # Other variables
        self.interpolator = Interpolator(interp_method)
        self.data = pd.DataFrame(columns=["t", self.var_name])
        self.consumer_thread = None
        self.running = False
        self.first_received = None

        self.start_consuming()

    def _start_consumer(self, server_url, port, group_id):
        """Creates and configures a Kafka consumer"""
        kafka_config = {
            "bootstrap.servers": f"{server_url}:{port}",
            "group.id": f"{group_id}_{self.var_name}",
            "enable.auto.commit": True,  # usage ?
            "auto.offset.reset": "earliest",  # usage ?
        }
        self.consumer = Consumer(kafka_config)

    def _lazy_subscribe(self):
        """One-time subscription"""
        if not self._subscribed:
            self.consumer.subscribe([self.topic])
            self._subscribed = True

    def _validate_config(self, config):
        """Parses configuration kwargs giving default values for optional arguments.

        Args:
            config (dict): keyword arguments dictionary.

        Returns:
            tuple: optional arguments as tuple.
        """

        # Optional arguments
        optional_args = (
            config.get("interpolation", "previous"),
            config.get("timeout", 2),
        )
        if "interpolation" not in config:
            logger.info(
                "Interpolation method not provided, using default 'previous' method."
            )
        if "timeout" not in config:
            logger.info("Timeout not provided, using default 2 seconds.")

        return optional_args

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
                if self.timeout >= 0:
                    logging.debug(
                        "First data recovered ('get_data')'. "
                        f"Shape: {data.shape}. "
                        f"Will wait {self.timeout} sec before proceeding."
                    )

                    # Wait and update data after timeout
                    time.sleep(self.timeout)
                    data = self.data.copy()

                    self.timeout = -1

                xp = data["t"]
                # xp = data.index
                yp = data[self.var_name]

                return self.interpolator(xp, yp, [t])

            except Exception as e:
                logger.error(f"Error: {e}")

            time.sleep(0.05)

    def send_data(self, data):
        """
        Send data to the Kafka topic.

        Args:
            data (str): data to send.
        """
        self.consumer.produce(self.topic, value=data)
        self.consumer.poll(0)
        self.consumer.flush()
        logger.info(f"Data sent to Kafka topic {self.topic}.")

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

    def _consume(self):
        """Run the consumer in a non-blocking mode."""
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1)
                if msg is None:
                    msg_list = None
                else:
                    msg_list = [msg]
                # msg_list = self.consumer.consume(timeout=0.5)

                if msg_list is None:
                    # time.sleep(0.01)
                    continue  # No new messages, continue polling

                for msg in msg_list:
                    self._handle_message(msg)

        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
        finally:
            self.consumer.close()

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
        except Exception as e:
            logger.error(f"Error handling messages: {e}")

    def start_consuming(self):
        """Start the consumer in a background thread."""
        try:
            if not self.running:
                self.running = True
                self.consumer_thread = threading.Thread(target=self._consume)
                self.consumer_thread.daemon = True
                self.consumer_thread.start()
                logger.info(f"Consumer thread started: {self.consumer_thread.name}")
        except Exception as e:
            logger.error(f"Error while start consuming messages: {e}")

    def stop_consuming(self):
        """Stop the consumer gracefully."""
        if self.running:
            self.running = False
            self.consumer_thread.join()  # Wait for the consumer thread to finish
            logger.info("Consumer thread stopped.")
