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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
import json
import logging
import pytest
import pandas as pd
import numpy as np
import pandas as pd
import pytest

from tests.data_stream_handler.mock_producer import MockProducerThreaded

logging.getLogger("cofmpy.data_stream_handler.kafka_data_stream_handler").setLevel(
    logging.DEBUG
)

# === Constants ===

DATA_1R = pd.DataFrame({"t": [0, 1.3, 2.9], "R": [1, 2.5, 1.2]})
DATA_2R = pd.DataFrame({"t": [0, 1.3, 2.9], "R1": [0.5, 10.0, 1.2], "R2": [0.5, 0, 5]})
RESISTOR_PATH = "Resistor.fmu"

FMUS = [
    {"id": "source", "path": "tests/data/source.fmu"},
    {"id": "resistor_1", "path": RESISTOR_PATH},
    {"id": "resistor_2", "path": RESISTOR_PATH},
]

TWO_RESISTORS_RESULTS = {
    ("source", "V"): {
        0.0: 0.0,
        0.05: 6.180339887498948,
        0.1: 11.755705045849464,
        0.15000000000000002: 16.18033988749895,
        0.2: 19.02113032590307,
        0.25: 20.0,
        0.3: 19.021130325903073,
        0.35: 16.18033988749895,
        0.39999999999999997: 11.755705045849465,
        0.44999999999999996: 6.180339887498959,
        0.49999999999999994: 1.1331077795295958e-14,
        0.5499999999999999: -6.180339887498938,
        0.6: -11.75570504584946,
        0.65: -16.180339887498945,
        0.7000000000000001: -19.02113032590307,
        0.7500000000000001: -20.0,
        0.8000000000000002: -19.021130325903066,
        0.8500000000000002: -16.18033988749894,
        0.9000000000000002: -11.755705045849439,
        0.9500000000000003: -6.180339887498919,
        1.0000000000000002: 3.06285495914156e-14,
        1.0500000000000003: 6.1803398874989774,
        1.1000000000000003: 11.755705045849487,
        1.1500000000000004: 16.180339887498974,
        1.2000000000000004: 19.021130325903087,
        1.2500000000000004: 20.0,
        1.3000000000000005: 19.02113032590305,
        1.3500000000000005: 16.18033988749891,
        1.4000000000000006: 11.755705045849412,
        1.4500000000000006: 6.180339887498888,
        1.5000000000000007: -6.37063927811259e-14,
        1.5500000000000007: -6.180339887499042,
        1.6000000000000008: -11.755705045849542,
        1.6500000000000008: -16.180339887499006,
        1.7000000000000008: -19.0211303259031,
        1.7500000000000009: -20.0,
        1.800000000000001: -19.02113032590304,
        1.850000000000001: -16.180339887498892,
        1.900000000000001: -11.755705045849357,
        1.950000000000001: -6.180339887498823,
        2.000000000000001: 9.67842359708362e-14,
        2.0500000000000007: 6.18033988749904,
        2.1000000000000005: 11.755705045849512,
        2.1500000000000004: 16.180339887498963,
        2.2: 19.02113032590308,
        2.25: 20.0,
        2.3: 19.021130325903087,
        2.3499999999999996: 16.180339887498974,
        2.3999999999999995: 11.75570504584953,
        2.4499999999999993: 6.180339887499061,
        2.499999999999999: 1.1882787835548857e-13,
        2.549999999999999: -6.180339887498835,
        2.5999999999999988: -11.75570504584934,
        2.6499999999999986: -16.180339887498835,
        2.6999999999999984: -19.021130325903002,
        2.7499999999999982: -20.0,
        2.799999999999998: -19.02113032590314,
        2.849999999999998: -16.180339887499102,
        2.8999999999999977: -11.755705045849705,
        2.9499999999999975: -6.180339887499267,
        2.9999999999999973: -3.699671294698183e-13,
        3.049999999999997: 6.180339887498563,
        3.099999999999997: 11.755705045849163,
        3.149999999999997: 16.18033988749871,
        3.1999999999999966: 19.021130325902934,
        3.2499999999999964: 20.0,
        3.2999999999999963: 19.02113032590323,
        3.349999999999996: 16.18033988749923,
        3.399999999999996: 11.755705045849878,
        3.4499999999999957: 6.180339887499471,
        3.4999999999999956: 5.855792437961431e-13,
        3.5499999999999954: -6.1803398874983575,
        3.599999999999995: -11.755705045848988,
        3.649999999999995: -16.180339887498583,
        3.699999999999995: -19.021130325902867,
        3.7499999999999947: -20.0,
        3.7999999999999945: -19.021130325903297,
        3.8499999999999943: -16.180339887499397,
        3.899999999999994: -11.755705045850053,
        3.949999999999994: -6.180339887499676,
    },
    ("resistor_1", "I_out"): {
        0.0: 0.0,
        0.05: 12.360679774997896,
        0.1: 23.511410091698927,
        0.15000000000000002: 32.3606797749979,
        0.2: 38.04226065180614,
        0.25: 40.0,
        0.3: 38.042260651806146,
        0.35: 32.3606797749979,
        0.39999999999999997: 23.51141009169893,
        0.44999999999999996: 12.360679774997918,
        0.49999999999999994: 2.2662155590591917e-14,
        0.5499999999999999: -12.360679774997877,
        0.6: -23.51141009169892,
        0.65: -32.36067977499789,
        0.7000000000000001: -38.04226065180614,
        0.7500000000000001: -40.0,
        0.8000000000000002: -38.04226065180613,
        0.8500000000000002: -32.36067977499788,
        0.9000000000000002: -23.511410091698878,
        0.9500000000000003: -12.360679774997838,
        1.0000000000000002: 6.12570991828312e-14,
        1.0500000000000003: 12.360679774997955,
        1.1000000000000003: 23.511410091698973,
        1.1500000000000004: 32.36067977499795,
        1.2000000000000004: 38.042260651806174,
        1.2500000000000004: 40.0,
        1.3000000000000005: 1.902113032590305,
        1.3500000000000005: 1.618033988749891,
        1.4000000000000006: 1.1755705045849412,
        1.4500000000000006: 0.6180339887498888,
        1.5000000000000007: -6.370639278112589e-15,
        1.5500000000000007: -0.6180339887499042,
        1.6000000000000008: -1.1755705045849543,
        1.6500000000000008: -1.6180339887499007,
        1.7000000000000008: -1.9021130325903102,
        1.7500000000000009: -2.0,
        1.800000000000001: -1.9021130325903042,
        1.850000000000001: -1.6180339887498891,
        1.900000000000001: -1.1755705045849356,
        1.950000000000001: -0.6180339887498822,
        2.000000000000001: 9.67842359708362e-15,
        2.0500000000000007: 0.618033988749904,
        2.1000000000000005: 1.1755705045849512,
        2.1500000000000004: 1.6180339887498962,
        2.2: 1.902113032590308,
        2.25: 2.0,
        2.3: 1.9021130325903086,
        2.3499999999999996: 1.6180339887498973,
        2.3999999999999995: 1.175570504584953,
        2.4499999999999993: 0.6180339887499061,
        2.499999999999999: 1.1882787835548857e-14,
        2.549999999999999: -0.6180339887498836,
        2.5999999999999988: -1.1755705045849338,
        2.6499999999999986: -1.6180339887498836,
        2.6999999999999984: -1.9021130325903002,
        2.7499999999999982: -2.0,
        2.799999999999998: -1.902113032590314,
        2.849999999999998: -1.6180339887499102,
        2.8999999999999977: -1.1755705045849705,
        2.9499999999999975: -5.1502832395827225,
        2.9999999999999973: -3.0830594122484863e-13,
        3.049999999999997: 5.150283239582135,
        3.099999999999997: 9.79642087154097,
        3.149999999999997: 13.483616572915594,
        3.1999999999999966: 15.850941938252445,
        3.2499999999999964: 16.666666666666668,
        3.2999999999999963: 15.850941938252692,
        3.349999999999996: 13.483616572916025,
        3.399999999999996: 9.796420871541565,
        3.4499999999999957: 5.150283239582893,
        3.4999999999999956: 4.879827031634525e-13,
        3.5499999999999954: -5.150283239581965,
        3.599999999999995: -9.796420871540823,
        3.649999999999995: -13.483616572915487,
        3.699999999999995: -15.85094193825239,
        3.7499999999999947: -16.666666666666668,
        3.7999999999999945: -15.850941938252747,
        3.8499999999999943: -13.483616572916164,
        3.899999999999994: -9.796420871541711,
        3.949999999999994: -5.1502832395830636,
    },
    ("resistor_2", "I_out"): {
        0.0: 0.0,
        0.05: 12.360679774997896,
        0.1: 23.511410091698927,
        0.15000000000000002: 32.3606797749979,
        0.2: 38.04226065180614,
        0.25: 40.0,
        0.3: 38.042260651806146,
        0.35: 32.3606797749979,
        0.39999999999999997: 23.51141009169893,
        0.44999999999999996: 12.360679774997918,
        0.49999999999999994: 2.2662155590591917e-14,
        0.5499999999999999: -12.360679774997877,
        0.6: -23.51141009169892,
        0.65: -32.36067977499789,
        0.7000000000000001: -38.04226065180614,
        0.7500000000000001: -40.0,
        0.8000000000000002: -38.04226065180613,
        0.8500000000000002: -32.36067977499788,
        0.9000000000000002: -23.511410091698878,
        0.9500000000000003: -12.360679774997838,
        1.0000000000000002: 6.12570991828312e-14,
        1.0500000000000003: 12.360679774997955,
        1.1000000000000003: 23.511410091698973,
        1.1500000000000004: 32.36067977499795,
        1.2000000000000004: 38.042260651806174,
        1.2500000000000004: 40.0,
        1.3000000000000005: 0.0,
        1.3500000000000005: 0.0,
        1.4000000000000006: 0.0,
        1.4500000000000006: 0.0,
        1.5000000000000007: 0.0,
        1.5500000000000007: 0.0,
        1.6000000000000008: 0.0,
        1.6500000000000008: 0.0,
        1.7000000000000008: 0.0,
        1.7500000000000009: 0.0,
        1.800000000000001: 0.0,
        1.850000000000001: 0.0,
        1.900000000000001: 0.0,
        1.950000000000001: 0.0,
        2.000000000000001: 0.0,
        2.0500000000000007: 0.0,
        2.1000000000000005: 0.0,
        2.1500000000000004: 0.0,
        2.2: 0.0,
        2.25: 0.0,
        2.3: 0.0,
        2.3499999999999996: 0.0,
        2.3999999999999995: 0.0,
        2.4499999999999993: 0.0,
        2.499999999999999: 0.0,
        2.549999999999999: 0.0,
        2.5999999999999988: 0.0,
        2.6499999999999986: 0.0,
        2.6999999999999984: 0.0,
        2.7499999999999982: 0.0,
        2.799999999999998: 0.0,
        2.849999999999998: 0.0,
        2.8999999999999977: 0.0,
        2.9499999999999975: -1.2360679774998533,
        2.9999999999999973: -7.399342589396366e-14,
        3.049999999999997: 1.2360679774997125,
        3.099999999999997: 2.3511410091698326,
        3.149999999999997: 3.2360679774997423,
        3.1999999999999966: 3.804226065180587,
        3.2499999999999964: 4.0,
        3.2999999999999963: 3.8042260651806457,
        3.349999999999996: 3.2360679774998458,
        3.399999999999996: 2.3511410091699756,
        3.4499999999999957: 1.2360679774998942,
        3.4999999999999956: 1.1711584875922861e-13,
        3.5499999999999954: -1.2360679774996715,
        3.599999999999995: -2.3511410091697975,
        3.649999999999995: -3.2360679774997165,
        3.699999999999995: -3.8042260651805733,
        3.7499999999999947: -4.0,
        3.7999999999999945: -3.8042260651806594,
        3.8499999999999943: -3.2360679774998795,
        3.899999999999994: -2.3511410091700107,
        3.949999999999994: -1.2360679774999352,
    },
}

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

# === Helper Functions ===


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


def make_literal_config(values, source_id="source_literal_na", unit="Ohm"):
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


# === Fixtures ===


@pytest.fixture
def kafka_resistor_test():

    var_name = "R"
    topic_name = "topic_1R"

    expected_values = np.array([1.0] * 13 + [2.5] * 16 + [1.2] * 11)

    mock_producer = MockProducerThreaded(
        DATA_1R,
        topic=topic_name,
        prev_delay=1,
        max_retries=100,
        end_thread=True,
        create_delay=0.1,
        send_delay=0.1,
        retry_delay=0.1,
    )

    kafka_config = make_kafka_config(var_name, topic=topic_name)

    return kafka_config, expected_values, mock_producer


@pytest.fixture
def kafka_two_resistors_test(generate_fmus):
    topic_name = "topic_2R"
    config = {
        "fmus": FMUS,
        "connections": SOURCE_CONNECTIONS
        + [
            make_source_target(make_kafka_config("R1", topic=topic_name), "resistor_1"),
            make_source_target(make_kafka_config("R2", topic=topic_name), "resistor_2"),
        ],
    }
    config.update(CONFIG_OPTIONS)

    producer = MockProducerThreaded(
        DATA_2R,
        topic_name,
        prev_delay=1,
        max_retries=50,
        end_thread=True,
        create_delay=0.1,
        send_delay=0.1,
        retry_delay=0.1,
    )

    return config, TWO_RESISTORS_RESULTS, producer


@pytest.fixture
def literal_two_resistors_test():
    config = {
        "fmus": FMUS,
        "connections": SOURCE_CONNECTIONS
        + [
            make_source_target(make_literal_config(DATA_2R["R1"]), "resistor_1"),
            make_source_target(make_literal_config(DATA_2R["R2"]), "resistor_2"),
        ],
    }
    config.update(CONFIG_OPTIONS)
    return config, TWO_RESISTORS_RESULTS


@pytest.fixture
def dummy_config(generate_backend_config_json):
    return {
        "uri": "localhost:9092",
        "topic": "test-topic",
        "group_id": "test-group",
        "interpolation": "previous",
        "variable": "value",
        "timeout": 0.1,
        "kafka_backend_conf": "backend_config.json",
    }


@pytest.fixture
def generate_backend_config_json(tmp_path):
    config_data = {
        "first_msg_timeout": 35,
        "retry_delay": 0.02,
        "first_delay": 4,
        "max_retries": 3,
        "offset_reset": "earliest",
        "max_buffer_len": 10,
        "thread_lifetime": np.inf,
    }
    file_path = tmp_path / "backend_config.json"
    with file_path.open("w") as f:
        json.dump(config_data, f)
    yield file_path


@pytest.fixture(scope="module")
def generate_csv(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("csv_test_data")

    csv_data = {
        "r1.csv": "t,variable\n0,0.5\n1.3,10.0\n2.9,1.2",
        "r2.csv": "t,variable\n0,0.5\n1.3,0.0\n2.9,5.0",
    }

    paths = []
    for fname, content in csv_data.items():
        path = base_dir / fname
        path.write_text(content)
        paths.append(path)

    yield paths


import os


@pytest.fixture(scope="module")
def generate_fmus():
    """
    Fixture to generate the FMU files before running tests (using pythonfmu).
    The FMUs are then deleted after the tests.
    """
    script_fnames = ("resistor_fmu.py",)
    fmu_fnames = ("Resistor.fmu",)

    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    for fmu_script in script_fnames:
        fmu_script_path = os.path.join(current_test_filepath, fmu_script)
        os.system(f"pythonfmu build -f {fmu_script_path} --no-external-tool")

    yield

    for fmu_file in fmu_fnames:
        os.remove(fmu_file)


@pytest.fixture
def csv_two_resistors_test(generate_csv, generate_fmus):
    r1_path, r2_path = generate_csv

    def make_csv_source(path):
        return {
            "type": "csv",
            "path": path,
            "variable": "variable",
            "unit": "Ohm",
            "id": "source_csv_na",
        }

    config = {
        "fmus": FMUS,
        "connections": SOURCE_CONNECTIONS
        + [
            make_source_target(make_csv_source(r1_path), "resistor_1"),
            make_source_target(make_csv_source(r2_path), "resistor_2"),
        ],
    }
    config.update(CONFIG_OPTIONS)

    return config, TWO_RESISTORS_RESULTS
