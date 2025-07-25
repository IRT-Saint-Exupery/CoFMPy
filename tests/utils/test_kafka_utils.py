import json
import time
import pytest
from unittest.mock import MagicMock

from cofmpy.data_stream_handler.kafka_utils import KafkaHandlerConfig, KafkaThreadManager, parse_kafka_message

# ====== KafkaHandlerConfig ======

def test_from_dict_without_json(base_config):
    config = KafkaHandlerConfig.from_dict(base_config)
    assert config.server_url == "localhost"
    assert config.port == "9092"
    assert config.topic == "my-topic"
    assert config.timeout == 0.1  # default


def test_from_dict_with_json_override(tmp_path, base_config):
    backend_data = {
        "timeout": 0.25,
        "retry_delay": 0.05,
        "first_msg_timeout": 10
    }

    json_path = tmp_path / "kafka_backend_config.json"
    json_path.write_text(json.dumps(backend_data))

    base_config["kafka_backend_conf"] = str(json_path)

    config = KafkaHandlerConfig.from_dict(base_config)
    assert config.timeout == 0.25
    assert config.retry_delay == 0.05
    assert config.first_msg_timeout == 10


def test_from_dict_with_missing_json_file(base_config):
    base_config["kafka_backend_conf"] = "nonexistent_file.json"
    config = KafkaHandlerConfig.from_dict(base_config)
    assert config.timeout == 0.1  # fallback to default


def test_from_dict_with_invalid_uri(base_config):
    base_config["uri"] = "localhost_only"
    with pytest.raises(IndexError):
        KafkaHandlerConfig.from_dict(base_config)


def test_from_dict_with_invalid_json(tmp_path, base_config):
    broken_json = tmp_path / "broken.json"
    broken_json.write_text("{ this is not json }")
    base_config["kafka_backend_conf"] = str(broken_json)

    with pytest.raises(json.JSONDecodeError):
        KafkaHandlerConfig.from_dict(base_config)

# ====== KafkaThreadManager ======

def test_kafka_thread_manager_runs_and_stops():
    mock_consumer = MagicMock()
    mock_consumer.poll.side_effect = [None, None, None]
    mock_consumer.close = MagicMock()

    callback_called = []

    def mock_callback(msg):
        callback_called.append(msg)

    manager = KafkaThreadManager(mock_consumer, mock_callback, thread_lifetime=0.2)
    manager.start()
    time.sleep(0.3)
    assert not manager.running
    mock_consumer.close.assert_called_once()


def test_kafka_thread_manager_callback_invoked():
    mock_consumer = MagicMock()

    # Simulate one real message, then None
    msg = MagicMock()
    mock_consumer.poll.side_effect = [msg, None, None]
    mock_consumer.close = MagicMock()

    received = []

    def callback(m):
        received.append(m)

    manager = KafkaThreadManager(mock_consumer, callback, thread_lifetime=0.5)
    manager.start()
    time.sleep(0.2)
    manager.stop()
    assert msg in received
    mock_consumer.close.assert_called_once()

# ====== parse_kafka_message ======

@pytest.mark.parametrize("payload,expected", [
    ('{"a": 1}', {"a": 1}),
    ("{'b': 2}", {"b": 2}),
    ('"just a string"', "just a string"),  # not a dict
    ("malformed json", "malformed json"),
])
def test_parse_kafka_message_valid_and_invalid(mock_msg, payload, expected):
    encoded = payload.encode("utf-8")
    msg = mock_msg(value=lambda: encoded)
    result = parse_kafka_message(msg)
    assert result == expected
