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
"""
Unit tests for the FixedPointInitializer class in cofmpy.utils.

This module tests the FixedPointInitializer class using various use cases. All methods
of the FixedPointInitializer are tested.

For the use case "math_fmus", the FMU is generated using the script `math_fmu.py` and
deleted after the tests are run.

- Use case 1: two interconnected identical math FMUs (with no internal state)
  - f(x) = 0.8*x + (1+u), where x is an internal input and u is an external input.
  - the two FMUs are identical and connects their output f(x) to the input x of the
    other FMU.
  - here, u=1 for the first FMU and u=-2 for the second FMU.
  - the expected FPI solution is: x=5/3 for the first FMU and x=10/3 for the second FMU.


TODO: We should add more use cases, especially with FMU with internal state (e.g. Dual
Mass Oscillator or Heat Controller) or with fixed input variables when there are more
degress of freedom than the number of equations.
"""

import os

import numpy as np
import pytest

from cofmpy import Coordinator
from cofmpy.utils import FixedPointInitializer


use_cases = [
    {  # Use case 1: two interconnected math FMUs
        "use_case_name": "math_fmus",
        "config": {
            "fmus": [
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
            ],
            "connections": [
                {
                    "source": {"id": "math1", "variable": "y"},
                    "target": {"id": "math2", "variable": "x"},
                },
                {
                    "source": {"id": "math2", "variable": "y"},
                    "target": {"id": "math1", "variable": "x"},
                },
            ],
        },
        "expected_results": {
            "updatable_inputs": [("math1", "x"), ("math2", "x")],
            "input_fmuid_varname2idx": {
                ("math1", "u"): 0,
                ("math1", "x"): 1,
                ("math2", "u"): 2,
                ("math2", "x"): 3,
            },
            "free_mask": [0, 1, 0, 1],
            "flattened_input": np.array([1, 20, -2, -1]),
            "fpi_solution": {
                "math1": {"u": [1], "x": [5 / 3]},
                "math2": {"u": [-2], "x": [10 / 3]},
            },
        },
    },
    {  # Use case 2: two interconnected FMUs, one with internal state
        "use_case_name": "internal_state_case",
        "config": {
            "fmus": [
                {
                    "id": "internal_state",
                    "path": "InternalStateFMU.fmu",
                    "initialization": {"x": 3},
                },
                {"id": "double", "path": "DoubleFMU.fmu"},
            ],
            "connections": [
                {
                    "source": {"id": "internal_state", "variable": "y"},
                    "target": {"id": "double", "variable": "u"},
                },
                {
                    "source": {"id": "double", "variable": "y"},
                    "target": {"id": "internal_state", "variable": "u"},
                },
            ],
        },
        "expected_results": {
            "updatable_inputs": [("internal_state", "u"), ("double", "u")],
            "input_fmuid_varname2idx": {("internal_state", "u"): 0, ("double", "u"): 1},
            "free_mask": [1, 1],
            "flattened_input": np.array([0, 0]),
            "fpi_solution": {
                "math1": {"u": [1], "x": [5 / 3]},
                "math2": {"u": [-2], "x": [10 / 3]},
            },
        },
    },
]


@pytest.fixture(scope="module", autouse=True)
def generate_fmus():
    """
    Fixture to generate the FMU files before running tests (using pythonfmu).
    The FMUs are then deleted after the tests.
    """
    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    for fmu_script in ("math_fmu.py", "internal_state_fmu.py", "double_fmu.py"):
        fmu_script_path = os.path.join(current_test_filepath, fmu_script)
        os.system(f"pythonfmu build -f {fmu_script_path} --no-external-tool")

    yield

    for fmu_file in ("MathFMU.fmu", "InternalStateFMU.fmu", "DoubleFMU.fmu"):
        os.remove(fmu_file)


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
    coordinator.start(conf_path=request.param["config"], fixed_point_init=False)
    return (
        coordinator,
        request.param["expected_results"],
    )


@pytest.fixture
def coordinator_instance(use_case):
    return use_case[0]


@pytest.fixture
def expected_results(use_case):
    return use_case[1]


@pytest.mark.parametrize(
    "solver,kwargs", [("fsolve", {"xtol": 1e-5}), ("root", {"jac": True})]
)
def test_fpi_constructor(coordinator_instance, expected_results, solver, kwargs):
    """
    Test the constructor __init__ of FixedPointInitializer.
    """

    fpi = FixedPointInitializer(
        coordinator_instance.master, solver, time_step=0.1, **kwargs
    )
    assert fpi.solver == solver
    assert fpi.time_step == 0.1
    assert fpi.kwargs == kwargs

    assert sorted(fpi.updatable_inputs) == sorted(expected_results["updatable_inputs"])
    assert fpi.input_fmuid_varname2idx == expected_results["input_fmuid_varname2idx"]
    assert (fpi.free_mask == expected_results["free_mask"]).all()


def test_fpi_flatten_dict(coordinator_instance, expected_results):
    """
    Test the flatten_dict and construct_from_flat methods of FixedPointInitializer.
    """
    fpi = FixedPointInitializer(coordinator_instance.master, "fsolve", time_step=1)

    # Flatten the input_dict
    input_dict = coordinator_instance.master.get_input_dict()
    flat = fpi._flatten_dict(input_dict)

    np.testing.assert_array_equal(flat, expected_results["flattened_input"])

    # Reconstruct the structured dictionary from the flat array
    structured = fpi._construct_from_flat(flat)
    assert structured == input_dict


def test_fpi_reset_fmus(coordinator_instance):
    """Test the _reset_fmus method of FixedPointInitializer."""
    fpi = FixedPointInitializer(coordinator_instance.master, "fsolve", time_step=1)

    fpi.master.current_time = 10.0
    fpi._reset_fmus()

    # Assert that master time was reset to 0
    assert fpi.master.current_time == 0


def test_fpi_solve(coordinator_instance, expected_results):
    """Test the solve method of FixedPointInitializer."""

    if "internal_state" in coordinator_instance.master.fmu_handlers.keys():
        pytest.skip("This test is not yet compatible with FMUs with internal state.")

    fpi = FixedPointInitializer(coordinator_instance.master, "fsolve", time_step=1)
    solution = fpi.solve()

    # Assert that the solution is a dictionary with the expected keys and values
    expected_solution = expected_results["fpi_solution"]
    assert solution.keys() == expected_solution.keys()
    for fmu_id, var_dict in solution.items():
        assert var_dict.keys() == expected_solution[fmu_id].keys()
        for var_name, value in var_dict.items():
            assert value == pytest.approx(expected_solution[fmu_id][var_name])
