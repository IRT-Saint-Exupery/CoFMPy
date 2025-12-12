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
import os
import pytest

from cofmupy import Coordinator

fmu_definitions = [
    {
        "id": "math1",
        "path": "MathFMU.fmu",
        "initialization": {"x": 20, "u": 1},
    },
    {
        "id": "math2",
        "path": "MathFMU.fmu",
        "initialization": {"x": -1, "u": -2},
    },
]
fmu_connections = [
    {
        "source": {"id": "math1", "variable": "y"},
        "target": {"id": "math2", "variable": "x"},
    },
    {
        "source": {"id": "math2", "variable": "y"},
        "target": {"id": "math1", "variable": "x"},
    },
]
# Use case with interconnected FMUs, and various options
use_cases = [
    {
        "use_case_name": "math_fmus_jacobi",
        "config": {
            "fmus": fmu_definitions,
            "connections": fmu_connections,
            "cosim_method": "jacobi",
        },
        "expected_results": {
            "first_sequence_order_fmu": "math1",
            "simulation": {
                "time": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
                ("math1", "y"): [
                    18.0,
                    0.5599999999999998,
                    12.72,
                    1.5584,
                    9.340800000000002,
                    2.197376,
                    7.178112000000002,
                    2.6063206400000003,
                    5.793991680000002,
                    2.8680452096000004,
                ],
                ("math2", "y"): [
                    -1.8,
                    13.4,
                    -0.552,
                    9.176000000000002,
                    0.24672000000000005,
                    6.472640000000002,
                    0.7579008000000003,
                    4.7424896000000025,
                    1.0850565120000004,
                    3.635193344000002,
                ],
            },
        },
    },
    {
        "use_case_name": "math_fmus_gauss_seidel",
        "config": {
            "fmus": fmu_definitions,
            "connections": fmu_connections,
            "cosim_method": "gauss_seidel",
        },
        "expected_results": {
            "first_sequence_order_fmu": "math1",
            "simulation": {
                "time": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
                ("math1", "y"): [
                    18.0,
                    12.72,
                    9.340800000000002,
                    7.178112000000002,
                    5.793991680000002,
                    4.908154675200002,
                    4.341218992128002,
                    3.978380154961922,
                    3.74616329917563,
                    3.5975445114724036,
                ],
                ("math2", "y"): [
                    13.4,
                    9.176000000000002,
                    6.472640000000002,
                    4.7424896000000025,
                    3.635193344000002,
                    2.926523740160002,
                    2.472975193702402,
                    2.182704123969538,
                    1.9969306393405044,
                    1.878035609177923,
                ],
            },
        },
    },
]


@pytest.fixture(scope="module", autouse=True)
def generate_fmu():
    """
    Fixture to generate the FMU files before running tests (using pythonfmu).
    The FMUs are then deleted after the tests.
    """
    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    fmu_script_path = os.path.join(current_test_filepath, "../data/math_fmu.py")
    os.system(f"pythonfmu build -f {fmu_script_path} --no-external-tool")

    yield

    os.remove("MathFMU.fmu")


@pytest.fixture(
    params=use_cases,
    ids=lambda param: param["use_case_name"],
)
def use_case(request):
    """
    Fixture for the use cases.

    The fixture is parametrized to test different use cases. It returns a tuple with:
    - an instance of the Coordinator (without fixed point initializer).
    - the expected results (dictionary)

    Returns:
        tuple: an instance of the Coordinator, and the expected results.
    """
    coordinator = Coordinator()
    return (
        coordinator,
        request.param["config"],
        request.param["expected_results"],
    )


@pytest.fixture
def coordinator_instance(use_case):
    return use_case[0]


@pytest.fixture
def coordinator_config(use_case):
    return use_case[1]


@pytest.fixture
def expected_results(use_case):
    return use_case[2]


def test_cosimulation(coordinator_instance, coordinator_config, expected_results):
    coordinator_instance.start(conf_path=coordinator_config, fixed_point_init=False)
    # Force sequence order with an array of array (instead of array of set)
    coordinator_instance.master.sequence_order = [["math1", "math2"]]
    assert (
        next(iter(coordinator_instance.master.sequence_order[0]))
        == expected_results["first_sequence_order_fmu"]
    )
    coordinator_instance.run_simulation(step_size=1, end_time=10)
    results_df = coordinator_instance.get_results()
    assert results_df == expected_results["simulation"]
