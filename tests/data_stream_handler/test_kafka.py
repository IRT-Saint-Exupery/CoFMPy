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
# test_kafka_data_stream_handler.py
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import pandas as pd
import time

from confluent_kafka import Consumer
from cofmupy.utils import Interpolator
from cofmupy.data_stream_handler import kafka_data_stream_handler
from cofmupy.data_stream_handler import KafkaDataStreamHandler
from cofmupy.data_stream_handler.kafka_utils import KafkaHandlerConfig
from cofmupy.data_stream_handler.kafka_utils import KafkaThreadManager


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def not_equiv_case():
    return [
        ("uri", "wrong_uri:1234"),
        ("topic", "wrong_topic"),
        ("group_id", "wrong_group"),
    ]


@pytest.fixture
def mock_consumer_and_thread_mgr():
    """
    Patches are needed to mock the kafka Consumer (no real Kafka message sending).
    Also thread manager is Mocked up.
    """
    with patch(
        "cofmupy.data_stream_handler.kafka_data_stream_handler.Consumer"
    ) as mock_consumer, patch(
        "cofmupy.data_stream_handler.kafka_data_stream_handler.KafkaThreadManager"
    ) as mock_thread_mgr:

        consumer_instance = MagicMock(spec=Consumer)
        mock_consumer.return_value = consumer_instance

        thread_manager_instance = MagicMock(spec=KafkaThreadManager)
        mock_thread_mgr.return_value = thread_manager_instance

        yield mock_consumer, consumer_instance, mock_thread_mgr, thread_manager_instance


@pytest.fixture
def fresh_handler_with_var(mock_consumer_and_thread_mgr, kafka_resistor_test):
    raw_config, _, _ = kafka_resistor_test
    _, consumer_instance, _, thread_manager_instance = mock_consumer_and_thread_mgr

    # raw_config is suited for Coordinator which uses ConfigParser.
    # We manually parse raw config to adapt it to KafkaDataStreamHandler
    for arg in ("type", "id", "unit"):
        _ = raw_config.pop(arg)
    var_name = raw_config.pop("variable")

    handler = KafkaDataStreamHandler(**raw_config)
    handler.thread_manager.running = PropertyMock(return_value=True)
    handler.add_variable(("any", "name"), var_name)

    return handler, var_name, raw_config


# -----------------------------
# Helper functions
# -----------------------------
def fake_time_controller(start: float, increment: float):
    current = {"t": start}

    def fake_time():
        current["t"] += increment
        return current["t"]

    return current, fake_time


def delayed_data_injection(handler, var_name, t_val=1.0, val=123):
    original = handler._build_out_dict

    def wrapper(t):
        if handler.data.empty:
            handler.data = pd.DataFrame({"t": [t_val], var_name: [val]})
        return original(t)

    handler._build_out_dict = wrapper


# -----------------------------
# Initialization & config tests
# -----------------------------
def test_init_and_config_validation(fresh_handler_with_var):
    h, _, _ = fresh_handler_with_var
    cfg = h.config

    assert isinstance(h.interpolator, Interpolator)
    assert h.interpolator.method == cfg.interpolation
    assert isinstance(h.config, KafkaHandlerConfig)
    assert isinstance(h.data, pd.DataFrame)
    assert isinstance(h.consumer, Consumer)
    assert isinstance(h.thread_manager, KafkaThreadManager)


def test_create_consumer_called_with_expected_config(fresh_handler_with_var):
    h, _, _ = fresh_handler_with_var
    expected_config = {
        "bootstrap.servers": f"{h.config.server_url}:{h.config.port}",
        "group.id": h.config.group_id,
        "enable.auto.commit": h.config.enable_auto_commit,
        "auto.offset.reset": h.config.auto_offset_reset,
    }
    kafka_data_stream_handler.Consumer.assert_called_once_with(expected_config)


# -----------------------------
# Lazy subscription
# -----------------------------
def test_lazy_subscribe_calls_consumer_once(fresh_handler_with_var):
    h, _, _ = fresh_handler_with_var
    c = h.consumer

    h._lazy_subscribe()
    c.subscribe.assert_called_once_with([h.config.topic])

    c.subscribe.reset_mock()
    h._lazy_subscribe()
    c.subscribe.assert_not_called()


# -----------------------------
# get_data tests
# -----------------------------
def test_get_data_waits_until_data_arrives(fresh_handler_with_var):
    h, var_name, _ = fresh_handler_with_var
    h.interpolator.__call__ = MagicMock(return_value=[123])

    delayed_data_injection(h, var_name)

    result = h.get_data(1.0)
    assert result == {("any", "name"): 123.0}


def test_get_data_respects_timeout_once(fresh_handler_with_var, monkeypatch):
    h, _, _ = fresh_handler_with_var
    h._build_out_dict = MagicMock(side_effect=lambda t: None)

    h.config.retry_delay = 0.01
    h.config.first_msg_timeout = 0.05

    start, fake_time = fake_time_controller(1000.0, 0.03)
    monkeypatch.setattr(time, "time", fake_time)

    result = h.get_data(1.0)

    assert result is None
    assert start["t"] >= 1000.0 + h.config.first_msg_timeout


# -----------------------------
# parse_kafka_message tests
# -----------------------------
@pytest.mark.parametrize(
    "msg_bytes,expected",
    [
        (
            b"{'t': 1.0, 'var1': 123, 'var2': 456}",
            {"t": [1.0], "var1": [123], "var2": [456]},
        ),
        (b"{}", {}),
    ],
)
def test_parse_kafka_message_valid_and_empty(
    fresh_handler_with_var, msg_bytes, expected
):
    h, _, _ = fresh_handler_with_var
    msg = MagicMock()
    msg.value.return_value = msg_bytes

    df = h.parse_kafka_message(msg)
    if expected:
        assert list(df.columns) == list(expected.keys())
        for k, v in expected.items():
            assert list(df[k]) == v
    else:
        assert df.empty


# -----------------------------
# Consumer thread control
# -----------------------------
def test_consumer_thread_start_stop(fresh_handler_with_var):
    h, _, _ = fresh_handler_with_var
    tm = h.thread_manager

    tm.start.assert_called_once()
    h.stop_consumer_thread()
    tm.stop.assert_called_once()


def test_thread_manager_received_correct_callback(fresh_handler_with_var):
    _, _, raw_config = fresh_handler_with_var
    with patch(
        "cofmupy.data_stream_handler.kafka_data_stream_handler.KafkaThreadManager"
    ) as mock_tm:
        h = KafkaDataStreamHandler(**raw_config)
        callback = mock_tm.call_args[0][1]
        assert callback == h._handle_message


# -----------------------------
# _handle_message tests
# -----------------------------
@pytest.mark.parametrize(
    "messages,expected_t,expected_val",
    [
        ([{"t": 1.0, "var1": 42}], [1.0], [42]),
        ([{"t": 1.0, "var1": 10}, {"t": 2.0, "var1": 20}], [1.0, 2.0], [10, 20]),
    ],
)
def test_handle_message_appends_multiple(
    fresh_handler_with_var, messages, expected_t, expected_val
):
    h, _, _ = fresh_handler_with_var

    for msg_dict in messages:
        # Ensure all keys exist as columns
        for k in msg_dict.keys():
            if k not in h.data.columns:
                h.data[k] = []

        msg = MagicMock()
        msg.value.return_value = str(msg_dict).encode()
        msg.error.return_value = None
        h._handle_message(msg)

    assert list(h.data["t"]) == expected_t
    var_name = [k for k in h.data.columns if k != "t"][0]
    assert list(h.data[var_name]) == expected_val


def test_handle_message_with_single_quotes(fresh_handler_with_var):
    h, var_name, _ = fresh_handler_with_var
    h.data = pd.DataFrame(columns=["t", var_name])

    msg = MagicMock()
    msg.value.return_value = f"{{'t': 1.0, '{var_name}': 99}}".encode()
    msg.error.return_value = None

    h._handle_message(msg)
    assert h.data[var_name].iloc[0] == 99


# -----------------------------
# is_equivalent_stream tests
# -----------------------------
def test_is_equivalent_stream_true(fresh_handler_with_var, kafka_resistor_test):
    h, _, _ = fresh_handler_with_var
    raw_config, _, _ = kafka_resistor_test
    assert h.is_equivalent_stream(**raw_config) is True


def test_is_equivalent_stream_false(
    fresh_handler_with_var, kafka_resistor_test, not_equiv_case
):
    h, _, _ = fresh_handler_with_var
    raw_config, _, _ = kafka_resistor_test

    for field, wrong_value in not_equiv_case:
        raw_config_copy = raw_config.copy()
        raw_config_copy[field] = wrong_value
        assert h.is_equivalent_stream(**raw_config_copy) is False
