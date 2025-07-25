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


def test_initialization(handler):
    assert handler.consumer is not None
    assert handler.config.topic == "test-topic"
    assert isinstance(handler.data, SortedDict)
    assert not handler._subscribed


def test_handle_message_stores_data(handler):
    handler.alias_mapping = {("node", "endpoint"): "variable"}

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

        result = handler.get_data(0.5)
        assert result is not None
        mock_interp.assert_called_once()


def test_is_equivalent_stream_matches(handler):
    config = {
        "config": {"uri": "localhost:9092", "topic": "test-topic", "group_id": "test-group"}
    }
    assert handler.is_equivalent_stream(config)


def test_is_equivalent_stream_mismatch(handler):
    config = {
        "config": {"uri": "wronghost:9092", "topic": "test-topic", "group_id": "test-group"}
    }
    assert not handler.is_equivalent_stream(config)
