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
import time
import pandas as pd
import numpy as np
import pytest
from cofmpy.data_stream_handler import KafkaDataStreamHandler
from tests.data_stream_handler.mock_producer import try_start_kafka_docker
from cofmpy.coordinator import Coordinator

docker_compose_path = "./tests/data_stream_handler/docker-compose.yml"

# try_start_kafka_docker(docker_compose_path, command="down")

has_kafka_started = try_start_kafka_docker(
    docker_compose_path, command="up", options="-d"
)

pytestmark = pytest.mark.skipif(
    not has_kafka_started, reason="Skipping test: kafka server is not running."
)

def test_kafka_resistor(kafka_resistor_test):

    config, expected_result, kafka_producer = kafka_resistor_test

    try_start_kafka_docker(docker_compose_path, command="up", options="-d")
    # Create and configure the handler

    # Start consuming with instantiation
    handler = KafkaDataStreamHandler(**config)

    # Start producer
    kafka_producer.start()

    # Collect interpolated results
    received = [handler.get_data(t / 10)[0] for t in range(40)]

    try_start_kafka_docker(docker_compose_path, command="down")

    assert np.isclose(received, expected_result).all(), "Mismatch in streamed vs expected data"

# pytest.skip("Skipping this test file", allow_module_level=True)

def test_kafka_two_resistors(kakfa_two_resistors_test):

    try_start_kafka_docker(docker_compose_path, command="up", options="-d")
    config, expected_results, kafka_producer = kakfa_two_resistors_test
    coordinator = Coordinator()
    kafka_producer.start()
    coordinator.start(config)
    for _ in range(80):
        coordinator.do_step(0.05)

    results = pd.DataFrame(coordinator.get_results())
    results = results.set_index("time")

    try_start_kafka_docker(docker_compose_path, command="down")

    assert results.to_dict() == expected_results
