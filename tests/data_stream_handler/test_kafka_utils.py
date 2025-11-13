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
import unittest
from unittest.mock import patch

from cofmpy.data_stream_handler.kafka_utils import KafkaHandlerConfig

import pytest

def test_valid_config():
    cfg = KafkaHandlerConfig(
        topic="my_topic",
        uri="localhost:9092",
        variable="var1",
        group_id="group1",
        timeout=0.5,
        interpolation="previous",
        auto_offset_reset="earliest",
        enable_auto_commit=False
    )
    assert cfg.server_url == "localhost"
    assert cfg.port == "9092"
    assert cfg.timeout == 0.5
    assert cfg.interpolation == "previous"
    assert cfg.auto_offset_reset == "earliest"
    assert cfg.enable_auto_commit is False

def test_missing_required_fields():
    with pytest.raises(TypeError):
        KafkaHandlerConfig(uri="localhost:9092", variable="var1")  # missing topic & group_id

def test_uri_splitting():
    cfg = KafkaHandlerConfig(topic="t", uri="127.0.0.1:1234", variable="v", group_id="g")
    assert cfg.server_url == "127.0.0.1"
    assert cfg.port == "1234"

def test_invalid_port():
    with pytest.raises(ValueError, match="Port must be numeric"):
        KafkaHandlerConfig(topic="t", uri="127.0.0.1:abc", variable="v", group_id="g")

def test_negative_timeout():
    with pytest.raises(ValueError, match="Timeout must be non-negative"):
        KafkaHandlerConfig(topic="t", uri="localhost:1234", variable="v", group_id="g", timeout=-1)

@pytest.mark.parametrize("offset", ["invalid", "start", "end"])
def test_invalid_auto_offset_reset(offset):
    with pytest.raises(ValueError, match="Invalid auto_offset_reset"):
        KafkaHandlerConfig(topic="t", uri="localhost:1234", variable="v", group_id="g", auto_offset_reset=offset)

@pytest.mark.parametrize("interp", ["unknown", "step"])
def test_invalid_interpolation(interp):
    with pytest.raises(ValueError, match="Invalid interpolation method"):
        KafkaHandlerConfig(topic="t", uri="localhost:1234", variable="v", group_id="g", interpolation=interp)

def test_malformed_uri():
    with pytest.raises(ValueError, match="Malformed URI"):
        KafkaHandlerConfig(topic="t", uri="justahost", variable="v", group_id="g")

# class TestKafkaHandlerConfig(unittest.TestCase):
#     def setUp(self):
#         self.valid_config_dict = {
#             "uri": "localhost:9092",
#             "topic": "test-topic",
#             "variable": "some-var",
#             "group_id": "group-123",
#         }

#     def test_valid_init(self):
#         config = KafkaHandlerConfig(
#             topic="topic1",
#             server_url="localhost",
#             port="9092",
#             group_id="group1",
#             variable="var1",
#             timeout=1.0,
#             interpolation="previous",
#             auto_offset_reset="earliest",
#             enable_auto_commit=True,
#         )
#         self.assertEqual(config.port, "9092")
#         self.assertEqual(config.timeout, 1.0)

#     def test_invalid_port(self):
#         with self.assertRaises(ValueError) as context:
#             KafkaHandlerConfig(
#                 topic="t",
#                 server_url="host",
#                 port="not-a-port",
#                 group_id="gid",
#                 variable="v",
#             )
#         self.assertIn("Port must be numeric", str(context.exception))

#     def test_negative_timeout(self):
#         with self.assertRaises(ValueError) as context:
#             KafkaHandlerConfig(
#                 topic="t",
#                 server_url="host",
#                 port="9092",
#                 group_id="gid",
#                 variable="v",
#                 timeout=-1,
#             )
#         self.assertIn("Timeout must be non-negative", str(context.exception))

#     def test_invalid_auto_offset_reset(self):
#         with self.assertRaises(ValueError) as context:
#             KafkaHandlerConfig(
#                 topic="t",
#                 server_url="host",
#                 port="9092",
#                 group_id="gid",
#                 variable="v",
#                 auto_offset_reset="unknown",
#             )
#         self.assertIn("Invalid auto_offset_reset", str(context.exception))

#     def test_invalid_interpolation(self):
#         with self.assertRaises(ValueError) as context:
#             KafkaHandlerConfig(
#                 topic="t",
#                 server_url="host",
#                 port="9092",
#                 group_id="gid",
#                 variable="v",
#                 interpolation="not-valid",
#             )
#         self.assertIn("Invalid interpolation method", str(context.exception))

#     def test_from_dict_valid(self):
#         config = KafkaHandlerConfig.from_dict(self.valid_config_dict)
#         self.assertEqual(config.server_url, "localhost")
#         self.assertEqual(config.port, "9092")

#     @patch("cofmpy.data_stream_handler.kafka_utils.logger")
#     def test_from_dict_missing_keys(self, mock_logger):
#         config = {"uri": "localhost:9092", "topic": "t"}
#         with self.assertRaises(KeyError):
#             KafkaHandlerConfig.from_dict(config)
#         mock_logger.error.assert_called()

#     def test_from_dict_malformed_uri(self):
#         config = {"uri": "localhost", "topic": "t", "group_id": "gid", "variable": "v"}
#         with self.assertRaises(ValueError) as context:
#             KafkaHandlerConfig.from_dict(config)
#         self.assertIn("Malformed URI", str(context.exception))


# if __name__ == "__main__":
#     unittest.main()
