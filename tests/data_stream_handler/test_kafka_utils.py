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

from cofmupy.data_stream_handler.kafka_utils import KafkaHandlerConfig

import pytest


def test_valid_config():
    cfg = KafkaHandlerConfig(
        topic="my_topic",
        uri="localhost:9092",
        group_id="group1",
        timeout=0.5,
        interpolation="previous",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    assert cfg.server_url == "localhost"
    assert cfg.port == "9092"
    assert cfg.timeout == 0.5
    assert cfg.interpolation == "previous"
    assert cfg.auto_offset_reset == "earliest"
    assert cfg.enable_auto_commit is False


def test_missing_required_fields():
    with pytest.raises(TypeError):
        KafkaHandlerConfig(uri="localhost:9092")  # missing topic & group_id


def test_uri_splitting():
    cfg = KafkaHandlerConfig(topic="t", uri="127.0.0.1:1234", group_id="g")
    assert cfg.server_url == "127.0.0.1"
    assert cfg.port == "1234"


def test_invalid_port():
    with pytest.raises(ValueError, match="Port must be numeric"):
        KafkaHandlerConfig(topic="t", uri="127.0.0.1:abc", group_id="g")


def test_negative_timeout():
    with pytest.raises(ValueError, match="Timeout must be non-negative"):
        KafkaHandlerConfig(topic="t", uri="localhost:1234", group_id="g", timeout=-1)


@pytest.mark.parametrize("offset", ["invalid", "start", "end"])
def test_invalid_auto_offset_reset(offset):
    with pytest.raises(ValueError, match="Invalid auto_offset_reset"):
        KafkaHandlerConfig(
            topic="t", uri="localhost:1234", group_id="g", auto_offset_reset=offset
        )


@pytest.mark.parametrize("interp", ["unknown", "step"])
def test_invalid_interpolation(interp):
    with pytest.raises(ValueError, match="Invalid interpolation method"):
        KafkaHandlerConfig(
            topic="t", uri="localhost:1234", group_id="g", interpolation=interp
        )


def test_malformed_uri():
    with pytest.raises(ValueError, match="Malformed URI"):
        KafkaHandlerConfig(topic="t", uri="justahost", group_id="g")
