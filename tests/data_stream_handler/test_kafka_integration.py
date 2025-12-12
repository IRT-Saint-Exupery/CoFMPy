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
"""
Integration test of KafkaDataStreamHandler using docker-compose for Kafka services.
"""
import numpy as np
from unittest.mock import patch
import pytest
import time

from cofmupy.data_stream_handler import KafkaDataStreamHandler
from tests.data_stream_handler.mock_producer import try_start_kafka_docker


class KafkaHandlerSeparated(KafkaDataStreamHandler):
    """Custom class to test one-handler-instance
    per Kafka topic ("separated") behaviour"""

    def _is_equivalent_stream(self, config):
        return False


# ====== Start Docker ======
docker_compose_path = "./tests/data_stream_handler/docker-compose.yml"

has_kafka_started = try_start_kafka_docker(
    docker_compose_path, command="up", options="-d"
)
time.sleep(0.1)

pytestmark = pytest.mark.skipif(
    not has_kafka_started, reason="Skipping test: kafka server is not running."
)


def test_kafka_resistor(kafka_resistor_test):

    config, expected_result, kafka_producer = kafka_resistor_test
    # var_name = config.get("variable")
    for arg in ("type", "id", "unit"):
        _ = config.pop(arg)
    var_name = config.pop("variable")
    fmu_var = ("fmu", "diagram_var")  # from the would-be diagram

    try_start_kafka_docker(docker_compose_path, command="up", options="-d")
    # Create and configure the handler

    # Start consuming with instantiation
    handler = KafkaDataStreamHandler(**config)
    handler.add_variable(fmu_var, var_name)
    time.sleep(0.1)

    # Start producer
    kafka_producer.start()

    # Collect interpolated results
    received = [handler.get_data(t / 10)[fmu_var] for t in range(40)]

    handler.thread_manager.stop()
    time.sleep(0.1)

    try_start_kafka_docker(docker_compose_path, command="down")

    assert np.isclose(
        received, expected_result
    ).all(), "Mismatch in streamed vs expected data"


def test_kafka_two_resistors_separated(kafka_two_resistors_test, run_integration_test):

    try_start_kafka_docker(docker_compose_path, command="up", options="-d")

    config, expected_results, kafka_producers = kafka_two_resistors_test(combined=False)
    _ = [m_prod.start() for m_prod in kafka_producers]
    with patch(
        "cofmupy.data_stream_handler.KafkaDataStreamHandler", KafkaHandlerSeparated
    ):
        run_integration_test(config, expected_results)
    time.sleep(0.1)

    try_start_kafka_docker(docker_compose_path, command="down")


def test_kafka_two_resistors_combined(kafka_two_resistors_test, run_integration_test):

    try_start_kafka_docker(docker_compose_path, command="up", options="-d")

    config, expected_results, kafka_producers = kafka_two_resistors_test(combined=True)
    _ = [m_prod.start() for m_prod in kafka_producers]
    run_integration_test(config, expected_results)
    time.sleep(0.1)

    try_start_kafka_docker(docker_compose_path, command="down")
