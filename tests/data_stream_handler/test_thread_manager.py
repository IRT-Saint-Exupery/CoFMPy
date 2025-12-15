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
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cofmupy.data_stream_handler.kafka_utils import KafkaThreadManager


@pytest.fixture
def mock_consumer():
    consumer = MagicMock()
    consumer.poll = MagicMock(return_value=None)
    return consumer


@pytest.fixture
def mock_callback():
    return MagicMock()


def test_start_initializes_thread(mock_consumer, mock_callback):
    manager = KafkaThreadManager(mock_consumer, mock_callback, thread_lifetime=2)

    # Patch Thread to prevent creating a real thread and allow assertions
    # Patch logger to check logging without printing to console
    # Patch time.time to control the start_time deterministically
    with patch(
        "cofmupy.data_stream_handler.kafka_utils.threading.Thread"
    ) as mock_thread, patch(
        "cofmupy.data_stream_handler.kafka_utils.logger"
    ) as mock_logger, patch(
        "cofmupy.data_stream_handler.kafka_utils.time.time", return_value=100
    ):

        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        manager.start()

        assert manager.running is True
        assert manager.start_time == 100
        mock_thread.assert_called_once_with(target=manager._consume_loop)
        thread_instance.start.assert_called_once()
        mock_logger.info.assert_called()


def test_consume_loop_stops_after_lifetime(mock_consumer, mock_callback):
    manager = KafkaThreadManager(mock_consumer, mock_callback, thread_lifetime=1)

    # Patch time.time to simulate elapsed time exceeding thread_lifetime
    # Patch logger to capture log calls
    with patch(
        "cofmupy.data_stream_handler.kafka_utils.time.time", side_effect=[0, 2]
    ), patch("cofmupy.data_stream_handler.kafka_utils.logger") as mock_logger:
        manager.running = True
        manager.start_time = 0

        manager._consume_loop()

        assert manager.running is False
        mock_logger.info.assert_any_call("Thread lifetime reached. Stopping thread.")
        mock_consumer.close.assert_called_once()


def test_consume_loop_processes_messages(mock_consumer, mock_callback):
    msg = MagicMock()
    mock_consumer.poll = MagicMock(side_effect=[msg, None, Exception("fail")])

    manager = KafkaThreadManager(mock_consumer, mock_callback, thread_lifetime=5)

    # Patch time.time to control elapsed time during the loop
    # Patch logger to capture info/error messages
    with patch(
        "cofmupy.data_stream_handler.kafka_utils.time.time", side_effect=[0, 0, 0, 6]
    ), patch("cofmupy.data_stream_handler.kafka_utils.logger") as mock_logger:
        manager.running = True
        manager.start_time = 0

        manager._consume_loop()

        mock_callback.assert_called_once_with(msg)
        mock_logger.error.assert_called_with(
            "Consumer error when polling message: fail"
        )
        mock_consumer.close.assert_called_once()


def test_stop_joins_thread(mock_consumer, mock_callback):
    manager = KafkaThreadManager(mock_consumer, mock_callback)
    fake_thread = MagicMock()
    manager.thread = fake_thread
    manager.running = True

    # Patch logger to verify log message when stopping thread
    with patch("cofmupy.data_stream_handler.kafka_utils.logger") as mock_logger:
        manager.stop()

        assert manager.running is False
        fake_thread.join.assert_called_once()
        mock_logger.info.assert_called_with("Kafka consumer thread stopped.")
