# conftest.py
import pytest
from collections import namedtuple
from pathlib import Path

@pytest.fixture
def base_config():
    return {
        "uri": "localhost:9092",
        "topic": "my-topic",
        "variable": "my-var",
        "group_id": "my-group",
    }

# @pytest.fixture
# def kafka_config_dict(tmp_path):
#     backend_conf = tmp_path / "backend_config.json"
#     backend_conf.write_text('{"first_msg_timeout": 0.2, "max_retries": 7}')
#     return {
#         "uri": "localhost:9092",
#         "topic": "my-topic",
#         "variable": "temp",
#         "group_id": "test-group",
#         "kafka_backend_conf": str(backend_conf),
#         "timeout": 0.05,
#     }

@pytest.fixture
def mock_msg():
    Msg = namedtuple("Msg", ["value"])
    return Msg
