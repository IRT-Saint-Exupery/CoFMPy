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
import time

import numpy as np
import pandas as pd
import pytest

from cofmpy.coordinator import Coordinator
from cofmpy.data_stream_handler import KafkaDataStreamHandler


@pytest.fixture(scope="module", autouse=True)
def kafka_docker():
    from tests.data_stream_handler.mock_producer import try_start_kafka_docker

    yml_path = "./tests/data_stream_handler/docker-compose.yml"

    # Start Kafka
    started = try_start_kafka_docker(yml_path, command="up", options="-d")
    if not started:
        pytest.skip("Kafka server did not start.")

    # Wait for Kafka to stabilize (can be tuned)
    time.sleep(5)

    yield  # Run tests

    # Tear down
    try_start_kafka_docker(yml_path, command="down")


def test_kafka_resistor(kafka_resistor_test):

    config, expected_values, kafka_producer = kafka_resistor_test
    conn_name = ("node", "endpoint")

    handler = KafkaDataStreamHandler(config)
    handler.add_variable(conn_name, config["variable"])

    kafka_producer.start()
    received_values = [handler.get_data(t / 10)[conn_name] for t in range(40)]

    assert np.isclose(received_values, expected_values).all(), "Mismatch in streamed vs expected data"


def test_kafka_two_resistors(kafka_two_resistors_test):
    config, expected_results, kafka_producer = kafka_two_resistors_test

    coordinator = Coordinator()
    kafka_producer.start()
    coordinator.start(config)

    for _ in range(80):
        coordinator.do_step(0.05)

    results = pd.DataFrame(coordinator.get_results()).set_index("time")
    assert results.to_dict() == expected_results
