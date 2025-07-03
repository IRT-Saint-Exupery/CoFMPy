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
Unit tests for the Master object.

The tests are based on the following use cases:
    1. Single FMU bouncing ball.
    2. Two FMUs with a single connection (source -> resistor).

TODO: Add more use cases to test different scenarios, especially with loops.
"""

from collections import defaultdict

import numpy as np
import pytest

from cofmpy.master import Master

use_cases = [
    {  # Use case 1: single FMU bouncing ball
        "use_case_name": "bouncing_ball",
        "master_config": {
            "fmu_config_list": [
                {
                    "id": "ball",
                    "path": "tests/wrappers/assets/BouncingBall.fmu",
                    "initialization": {"e": 0.6},  # coefficient of restitution
                }
            ],
            "connections": {},
            "sequence_order": [["ball"]],
        },
        "expected_results": {
            "fmu_ids": ["ball"],
            "input_dict_first_fmu": np.array(0),
            "input_dict": {"ball": {}},
            "output_vars": {"ball": ["h", "v"]},
            "do_step": {"ball": {"h": [0.951440], "v": [-0.9809999]}},
            "results_keys": [("ball", "h"), ("ball", "v")],
            "new_var_value": ("ball", None, None),  # No input variable for FMU "ball"
            "loop_fmu_ids": ["ball"],
        },
    },
    {  # Use case 2: two FMUs with a single connection (source -> resistor)
        "use_case_name": "source_resistor",
        "master_config": {
            "fmu_config_list": [
                {
                    "id": "source",
                    "path": "tests/data/source.fmu",
                    "initialization": {"phase": 0.9},
                },
                {
                    "id": "resistor",
                    "path": "tests/data/resistor.fmu",
                    "initialization": {"R": 5.0},
                },
            ],
            "connections": {("source", "V"): [("resistor", "V")]},
            "sequence_order": [["source"], ["resistor"]],
        },
        "expected_results": {
            "fmu_ids": ["source", "resistor"],
            "input_dict_first_fmu": np.array(0),
            "input_dict": {"source": {}, "resistor": {"V": [0]}},
            "output_vars": {"source": ["V"], "resistor": ["I"]},
            "do_step": {"source": {"V": [15.666538]}, "resistor": {"I": [3.133307]}},
            "results_keys": [("source", "V"), ("resistor", "I")],
            "new_var_value": ("resistor", "V", 3.0),
            "loop_fmu_ids": ["source", "resistor"],
        },
    },
]


@pytest.fixture(
    params=use_cases,
    ids=lambda param: param["use_case_name"],
)
def use_case(request):
    """
    Fixture for the use cases.

    The fixture is parametrized to test different use cases. It returns a tuple with:
    - an instance of the Master.
    - the expected results (dictionary)

    Returns:
        tuple: an instance of the Master class, and the expected results.
    """
    return Master(**request.param["master_config"]), request.param["expected_results"]


@pytest.fixture
def master_instance(use_case):
    return use_case[0]


@pytest.fixture
def expected_results(use_case):
    return use_case[1]


def test_master_initialization(master_instance, expected_results):
    """
    Asserts that the Master class instance is correctly initialized (attributes and
    types).
    """
    assert master_instance.fmu_config_list is not None
    assert master_instance.connections is not None
    assert master_instance.sequence_order is not None
    assert list(master_instance.fmu_handlers.keys()) == expected_results["fmu_ids"]
    assert master_instance.current_time == None
    assert isinstance(master_instance._input_dict, dict)
    assert isinstance(master_instance._output_dict, dict)
    assert isinstance(master_instance._results, defaultdict)


def test_check_connections_valid_config(master_instance):
    """
    Test that _check_connections() passes silently for valid FMU connections.
    """
    master_instance._check_connections()


def test_check_connections_invalid_source_variable(master_instance):
    """
    Test that _check_connections() raises ValueError if the source variable is invalid.
    """
    src_fmu = list(master_instance.fmu_handlers.keys())[0]
    # Inject an invalid source variable for the first FMU
    master_instance.connections = {(src_fmu, "nonexistent_output"): []}

    with pytest.raises(
        ValueError,
        match=(
            "Source variable 'nonexistent_output' not found in "
            f"outputs of FMU '{src_fmu}': *"
        ),
    ):
        master_instance._check_connections()


def test_check_connections_invalid_target_variable(master_instance, expected_results):
    """
    Test that check_connections() raises ValueError if the target variable is invalid.
    """
    # Create a dummy connection with an invalid target variable
    fmu_ids = list(master_instance.fmu_handlers.keys())
    src_fmu, tgt_fmu = fmu_ids[0], fmu_ids[-1]  # -1 = 0 for a single FMU (e.g. ball)
    src_var = expected_results["output_vars"][src_fmu][0]

    master_instance.connections = {
        (src_fmu, src_var): [(tgt_fmu, "nonexistent_input")]
    }

    with pytest.raises(
        ValueError,
        match=(
            "Target variable 'nonexistent_input' not found in "
            f"inputs of FMU '{tgt_fmu}': *"
        ),
    ):
        master_instance._check_connections()


def test_init_simulation(master_instance, expected_results):
    """
    Asserts that the simulation is correctly initialized and that the input dictionary
    is correctly set.
    """
    master_instance.init_simulation()
    assert master_instance.current_time == 0.0

    # Assert that the input_dict is correctly set
    assert master_instance.get_input_dict() == expected_results["input_dict"]

    # Assert that the output_dict is correctly set
    outputs = master_instance.get_outputs()
    assert isinstance(outputs, dict)
    assert outputs.keys() == master_instance.fmu_handlers.keys()
    for fmu_id, fmu_out in master_instance.get_outputs().items():
        assert list(fmu_out.keys()) == expected_results["output_vars"][fmu_id]


def test_set_inputs(master_instance, expected_results):
    """
    Asserts that the input dictionary is correctly set and that the inputs can be
    modified after the initialization of the simulation (not before).
    """
    first_fmu_name = list(master_instance.fmu_handlers.keys())[0]

    # Assert that the input dictionary before initialization is as expected (np.zeros)
    expected_fmu_input = expected_results["input_dict_first_fmu"]
    if len(expected_fmu_input.shape) > 0:
        assert master_instance._input_dict[first_fmu_name] == expected_fmu_input

    # Assert that set_inputs() before initialization raises a RuntimeError
    with pytest.raises(RuntimeError):
        master_instance.set_inputs()

    # Assert that `set_inputs()` (with empty arg) after initialization works
    master_instance.init_simulation()
    master_instance.set_inputs()
    assert master_instance._input_dict == expected_results["input_dict"]

    # Assert that `set_inputs(something)` after initialization works (if the FMU has an
    # input variable)
    fmu_id, var_name, new_value = expected_results["new_var_value"]
    if var_name is not None:
        master_instance.set_inputs({fmu_id: {var_name: [new_value]}})
        assert master_instance._input_dict[fmu_id][var_name] == [new_value]

    # Assert that setting with a wrong fmu name raises an error
    with pytest.raises(ValueError, match="FMU 'dummy_fmu' not found in FMUs"):
        master_instance.set_inputs({"dummy_fmu": {"dummy_var": [3.0]}})

    # Assert that setting with a wrong variable name raises an error
    with pytest.raises(ValueError, match="Variable 'dummy_var' not found in inputs"):
        master_instance.set_inputs({fmu_id: {"dummy_var": [12.0]}})


def test_solve_loop_jacobi(master_instance, expected_results):
    """Asserts that the solve_loop method works. The solve_loop method only runs the
    step method of the FMUs. The results are not checked here.
    """
    loop_fmu_ids = expected_results["loop_fmu_ids"]

    step_size = 0.01
    master_instance.init_simulation()

    with pytest.raises(NotImplementedError):
        master_instance.solve_loop(loop_fmu_ids, step_size, algo="invalid_algo")

    output = master_instance.solve_loop(loop_fmu_ids, step_size, algo="jacobi")
    assert isinstance(output, dict)
    assert list(output.keys()) == loop_fmu_ids


def test_do_step(master_instance, expected_results):
    """
    Asserts that the do_step method works. The results are checked against the expected
    results.
    """
    # Raises an error if the simulation is not initialized
    with pytest.raises(RuntimeError):
        master_instance.do_step(step_size=0.1)

    # Run a single step. Assert that the results are as expected.
    master_instance.init_simulation()
    output = master_instance.do_step(step_size=0.1)

    assert master_instance.current_time == 0.1
    assert isinstance(output, dict)
    assert [k in output.keys() for k in master_instance.fmu_handlers.keys()]
    print(output)
    for fmu_id, output_vars in output.items():
        for var_name, val in output_vars.items():
            assert val == pytest.approx(expected_results["do_step"][fmu_id][var_name])

    # Run another step. Assert that the time is correctly updated.
    output = master_instance.do_step(step_size=0.25)
    assert master_instance.current_time == 0.35
