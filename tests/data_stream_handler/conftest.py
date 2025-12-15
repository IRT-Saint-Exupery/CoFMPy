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
import numpy as np
import pandas as pd
import pytest

from .two_resistor_values import TWO_RESISTORS_RESULTS
from cofmupy.coordinator import Coordinator
from tests.data_stream_handler.mock_producer import MockProducerThreaded

# ====== Constants ======

DATA_1R = pd.DataFrame({"t": [0, 1.3, 2.9], "R": [1, 2.5, 1.2]})
DATA_2R = pd.DataFrame({"t": [0, 1.3, 2.9], "R1": [0.5, 10.0, 1.2], "R2": [0.5, 0, 5]})


FMUS = [
    {"id": "source", "path": "tests/data/source.fmu"},
    {"id": "resistor_1", "path": "tests/data/resistor3.fmu"},
    {"id": "resistor_2", "path": "tests/data/resistor3.fmu"},
]

CONFIG_OPTIONS = {
    "root": "",
    "loop_solver": "jacobi",
    "edge_sep": " -> ",
}

SOURCE_CONNECTIONS = [
    {
        "source": {"id": "source", "variable": "V", "unit": "V", "type": "fmu"},
        "target": {"id": "resistor_1", "variable": "V_in", "unit": "V", "type": "fmu"},
    },
    {
        "source": {"id": "source", "variable": "V", "unit": "V", "type": "fmu"},
        "target": {"id": "resistor_2", "variable": "V_in", "unit": "V", "type": "fmu"},
    },
]

# ====== Fixtures ======


@pytest.fixture(scope="module")
def generate_csv(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("csv_test_data")

    csv_data = {
        "r1.csv": "t,r1\n0,0.5\n1.3,10.0\n2.9,1.2",
        "r2.csv": "t,r2\n0,0.5\n1.3,0.0\n2.9,5.0",
        "resistors.csv": "t,r1,r2\n0,0.5,0.5\n1.3,10.0,0.0\n2.9,1.2,5.0",
    }

    paths = []
    for fname, content in csv_data.items():
        path = base_dir / fname
        path.write_text(content)
        paths.append(path)

    yield paths


# ====== Helper Functions ======


def make_local_config(values, source_id="source_literal_na", unit="Ohm"):
    return {
        "type": "literal",
        "values": {str(t): v for t, v in zip(DATA_2R["t"], values)},
        "unit": unit,
        "id": source_id,
    }


def make_source_target(source, target_id):
    return {
        "source": source,
        "target": {"id": target_id, "variable": "R", "unit": "Ohm", "type": "fmu"},
    }


def make_csv_source(path, var_name="variable"):
    return {
        "type": "csv",
        "path": path,
        "variable": var_name,
        "unit": "Ohm",
        "id": "source_csv_na",
    }


def make_kafka_config(
    variable,
    topic="dummy_topic",
    uri="localhost:9092",
    group_id="my_group",
    interpolation="previous",
    unit="Ohm",
    timeout=2,
    backend_conf_path="",
    first_msg_timeout=35,
    max_retries=3,
    retry_delay=0.05,
    first_delay=0.5,
    offset_reset="earliest",
    max_buffer_len=10,
    thread_lifetime=np.inf,
):
    return {
        "type": "kafka",
        "uri": uri,
        "topic": topic,
        "group_id": group_id,
        "variable": variable,
        "unit": unit,
        "interpolation": interpolation,
        "id": f"source_kafka_{variable}",
        "timeout": timeout,
        "backend_conf_path": backend_conf_path,
        "first_msg_timeout": first_msg_timeout,
        "max_retries": max_retries,
        "retry_delay": retry_delay,
        "first_delay": first_delay,
        "offset_reset": offset_reset,
        "max_buffer_len": max_buffer_len,
        "thread_lifetime": thread_lifetime,
    }


def make_producer(
    data,
    topic_name,
    prev_delay=1,
    max_retries=100,
    end_thread=True,
    create_delay=0.1,
    send_delay=0.1,
    retry_delay=0.1,
):

    return MockProducerThreaded(
        data,
        topic=topic_name,
        prev_delay=prev_delay,
        max_retries=max_retries,
        end_thread=end_thread,
        create_delay=create_delay,
        send_delay=send_delay,
        retry_delay=retry_delay,
    )


# ====== Integration tests fixtures ======
@pytest.fixture
def run_integration_test():
    def _make(config, expected_res):
        coordinator = Coordinator()
        coordinator.start(config)

        for _ in range(80):
            coordinator.do_step(0.05)

        results = dict(coordinator.get_results())
        assert results == expected_res

        for sh in coordinator.stream_handlers:
            try:
                sh.thread_manager.stop()
            except:
                pass

    return _make


# ====== Csv test fixtures ======


@pytest.fixture
def csv_two_resistors_test(generate_csv):

    def _make(combined=False):
        r1_path, r2_path, r1_r2_path = generate_csv

        if combined:
            pths = (r1_r2_path, r1_r2_path)
        else:
            pths = (r1_path, r2_path)

        r_connections = [
            make_source_target(make_csv_source(pths[0], "r1"), "resistor_1"),
            make_source_target(make_csv_source(pths[1], "r2"), "resistor_2"),
        ]

        config = {
            "fmus": FMUS,
            "connections": SOURCE_CONNECTIONS + r_connections,
        }
        config.update(CONFIG_OPTIONS)

        return config, TWO_RESISTORS_RESULTS

    return _make


# ====== Literal test fixtures ======


@pytest.fixture
def local_two_resistors_test():
    config = {
        "fmus": FMUS,
        "connections": SOURCE_CONNECTIONS
        + [
            make_source_target(make_local_config(DATA_2R["R1"]), "resistor_1"),
            make_source_target(make_local_config(DATA_2R["R2"]), "resistor_2"),
        ],
    }
    config.update(CONFIG_OPTIONS)
    return config, TWO_RESISTORS_RESULTS


# ====== Kafka test fixtures ======


@pytest.fixture
def kafka_resistor_test():

    var_name = "R"
    topic_name = "topic_1R"

    expected_values = np.array([1.0] * 13 + [2.5] * 16 + [1.2] * 11)

    mock_producer = make_producer(DATA_1R, topic_name)
    kafka_config = make_kafka_config(var_name, topic=topic_name)

    return kafka_config, expected_values, mock_producer


@pytest.fixture
def kafka_two_resistors_test():

    def _make(combined=False):

        var_names = ("R1", "R2")
        topic_names = ("2Rs_a", "2Rs_b")

        if combined:
            topic_names = (topic_names[0], topic_names[0])
            mock_producers = [make_producer(DATA_2R, topic_names[0])]

        else:
            mock_producers = [make_producer(DATA_2R, tn) for tn in topic_names]

        r_connections = [
            make_source_target(
                make_kafka_config(var_names[0], topic=topic_names[0]), "resistor_1"
            ),
            make_source_target(
                make_kafka_config(var_names[1], topic=topic_names[1]), "resistor_2"
            ),
        ]

        kafka_config = {
            "fmus": FMUS,
            "connections": SOURCE_CONNECTIONS + r_connections,
        }
        kafka_config.update(CONFIG_OPTIONS)

        return kafka_config, TWO_RESISTORS_RESULTS, mock_producers

    return _make
