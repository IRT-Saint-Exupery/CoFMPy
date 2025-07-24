<<<<<<< HEAD
# -*- coding: utf-8 -*-
# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
# The 2-Clause BSD License
#
=======
# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
>>>>>>> 851984e (add support for multiple data streams grouped by data handler, update tests)
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
<<<<<<< HEAD
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# test_kafka_data_stream_handler.py
import pytest

pytest.skip("Skipping this test file", allow_module_level=True)
import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import json
import threading
from cofmpy.data_stream_handler import KafkaDataStreamHandler


class TestKafkaDataStreamHandler(unittest.TestCase):
    def setUp(self):
        self.var_name = "MySignal"
        self.topic = "test_topic"
        self.t_out = 1
        self.config = {
            "topic": self.topic,
            "variable": self.var_name,
            "uri": "localhost:9092",
            "group_id": "test_group",
            "interpolation": "previous",
            "timeout": self.t_out,
        }

    @patch(
        "cofmpy.data_stream_handler.kafka_data_stream_handler.KafkaDataStreamHandler.start_consuming"
    )
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Interpolator")
    def test_init_and_config_validation(self, mock_interp, mock_consumer, mock_start):
        handler = KafkaDataStreamHandler(**self.config)
=======
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
from unittest.mock import patch, MagicMock
import pytest
from cofmpy.data_stream_handler.kafka_data_stream_handler import KafkaDataStreamHandler

from sortedcontainers import SortedDict


@pytest.fixture
def handler(dummy_config):
    with patch(
        "cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer"
    ) as mock_consumer, patch(
        "cofmpy.data_stream_handler.kafka_data_stream_handler.KafkaThreadManager"
    ) as mock_thread_mgr:

        mock_consumer.return_value = MagicMock()
        mock_thread_mgr.return_value = MagicMock()
        return KafkaDataStreamHandler(dummy_config)

>>>>>>> 851984e (add support for multiple data streams grouped by data handler, update tests)

def test_initialization(handler):
    assert handler.consumer is not None
    assert handler.config.topic == "test-topic"
    assert isinstance(handler.data, SortedDict)
    assert not handler._subscribed


<<<<<<< HEAD
    def test_validate_config_defaults(self):
        config = {"topic": "t", "variable": "v", "uri": "server:1234", "group_id": "g"}
        handler_args = KafkaDataStreamHandler._validate_config(
            KafkaDataStreamHandler, config
        )
        positional, optional = handler_args
=======
def test_handle_message_stores_data(handler):
    handler.alias_mapping = {("node", "endpoint"): "variable"}
>>>>>>> 851984e (add support for multiple data streams grouped by data handler, update tests)

    fake_message = {"t": 1.0, "variable": 42.0}

    with patch(
        "cofmpy.data_stream_handler.kafka_data_stream_handler.parse_kafka_message",
        return_value=fake_message,
    ):
        msg = MagicMock()
        msg.error.return_value = None

        handler._handle_message(msg)
        assert 1.0 in handler.data
        assert handler.data[1.0]["variable"] == 42.0


def test_lazy_subscribe_subscribes_once(handler):
    handler._lazy_subscribe()
    handler.consumer.subscribe.assert_called_once_with(["test-topic"])
    assert handler._subscribed

    # Calling again shouldn't resubscribe
    handler._lazy_subscribe()
    handler.consumer.subscribe.assert_called_once()  # still only once


def test_get_data_returns_interpolated_value(handler):
    # Setup: inject mock data and mock interpolator
    handler.alias_mapping = {("node", "endpoint"): "variable"}
    handler._subscribed = True
    handler.thread_manager.running = True

    handler.data[0.0] = {"variable": 1.0}
    handler.data[1.0] = {"variable": 2.0}

    with patch(
        "cofmpy.data_stream_handler.kafka_data_stream_handler.lookup_with_window",
        return_value=(True, [0.0, 1.0], [{"variable": 1.0}, {"variable": 2.0}]),
    ), patch.object(handler, "interpolator", return_value=[{"node": 2.0}]) as mock_interp:

<<<<<<< HEAD
        handler.data = pd.DataFrame({"t": [1.0, 2.0, 3.0], "value": [20.0, 21.0, 22.0]})

        handler.timeout = -1  # Skip sleep logic

        mock_interp = MagicMock()
        mock_interp.return_value = [21.5]
        handler.interpolator = mock_interp

        result = handler.get_data(2.5)
        mock_interp.assert_called_once()
        self.assertEqual(result, [21.5])

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.logger")
    def test_handle_message_with_error(self, mock_logger):
        mock_message = MagicMock()
        mock_message.error.return_value = MagicMock(code=lambda: 1)
=======
        result = handler.get_data(0.5)
        assert result is not None
        mock_interp.assert_called_once()
>>>>>>> 851984e (add support for multiple data streams grouped by data handler, update tests)


def test_is_equivalent_stream_matches(handler):
    config = {
        "config": {"uri": "localhost:9092", "topic": "test-topic", "group_id": "test-group"}
    }
    assert handler.is_equivalent_stream(config)

<<<<<<< HEAD
        mock_logger.error.assert_called()

    def test_handle_message_valid(self):
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b"{'t': 1, 'temperature': 22}"
        mock_message.offset.return_value = 5

        handler = KafkaDataStreamHandler(**self.config)
        handler.data = pd.DataFrame(columns=["t", "temperature"])
        handler.first_received = None

        handler._handle_message(mock_message)
        self.assertIsNotNone(handler.first_received)
        self.assertIn("temperature", handler.data.columns)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_start_stop_consuming(self, mock_consumer_class):
        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()

        handler.start_consuming()
        self.assertTrue(handler.running)
        self.assertTrue(handler.consumer_thread.is_alive())

        handler.stop_consuming()
        self.assertFalse(handler.running)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_consume_loop(self, mock_consumer_class):
        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()
        handler.running = True

        # Simulate poll returning one mock message
        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"{'t': 1, 'temperature': 22}"
        mock_msg.offset.return_value = 3
        handler.consumer.poll = MagicMock(side_effect=[mock_msg, None, None])
        handler._handle_message = MagicMock()
        handler.consumer.close = MagicMock()

        # Run _consume for a short time
        def stop_soon():
            handler.running = False

        threading.Timer(0.1, stop_soon).start()
        handler._consume()

        handler._handle_message.assert_called_with(mock_msg)
=======

def test_is_equivalent_stream_mismatch(handler):
    config = {
        "config": {"uri": "wronghost:9092", "topic": "test-topic", "group_id": "test-group"}
    }
    assert not handler.is_equivalent_stream(config)
>>>>>>> 851984e (add support for multiple data streams grouped by data handler, update tests)
