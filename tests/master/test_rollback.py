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

from cofmupy.master import Master


@pytest.fixture(scope="module", autouse=True)
def generate_fmu():
    """
    Fixture to generate the FMU files before running tests (using pythonfmu).
    The FMUs are then deleted after the tests.
    """
    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    fmu_script_path = os.path.join(current_test_filepath, "../data/math_fmu.py")
    os.system(f"pythonfmu build -f {fmu_script_path} --no-external-tool")

    fmu_script_path = os.path.join(current_test_filepath, "../data/math_fmu_v3_bad.py")
    os.system(f"pythonfmu3 build -f {fmu_script_path} --no-external-tool")
    fmu_script_path = os.path.join(current_test_filepath, "../data/math_fmu_v3.py")
    os.system(
        f"pythonfmu3 build -f {fmu_script_path} --no-external-tool --handle-state"
    )

    yield

    os.remove("MathFMU.fmu")
    os.remove("MathFMUV3Bad.fmu")
    os.remove("MathFMUV3.fmu")


def test_fmu_for_cosimulation():
    correct_config = {
        "fmu_config_list": [
            {
                "id": "math1",
                "path": "MathFMU.fmu",
                "initialization": {"x": -1, "u": -2},
            }
        ],
        "connections": {},
        "sequence_order": [],
    }
    master = Master(**correct_config)


def test_rollback_v2():
    correct_config = {
        "fmu_config_list": [
            {
                "id": "math1",
                "path": "MathFMU.fmu",
                "initialization": {"x": -1, "u": -2},
            },
            {
                "id": "math2",
                "path": "MathFMU.fmu",
                "initialization": {"x": 20, "u": 1},
            },
        ],
        "connections": {
            ("math1", "y"): [("math2", "x")],
            ("math2", "y"): [("math1", "x")],
        },
        "sequence_order": [["math1", "math2"]],
    }
    master = Master(**correct_config)
    math1_handler = master.fmu_handlers["math1"]

    math1_handler.set_variables({"u": [8]})
    math1_handler.set_variables({"x": [11]})
    outputs = {}
    outputs["0"] = math1_handler.step(0, 1, {})
    outputs["1"] = math1_handler.step(1, 1, {})
    outputs["2"] = math1_handler.step(2, 1, {})
    state = math1_handler.get_state()
    math1_handler.step(3, 1, {})
    math1_handler.set_state(state)
    math1_handler.set_variables({"u": [6]})
    math1_handler.set_variables({"x": [25]})
    outputs["3"] = math1_handler.step(3, 1, {})

    assert outputs == {
        "0": {"y": [17.8]},
        "1": {"y": [17.8]},
        "2": {"y": [17.8]},
        "3": {"y": [27.0]},
    }


def test_rollback_v3():
    correct_config = {
        "fmu_config_list": [
            {
                "id": "math1",
                "path": "MathFMUV3.fmu",
                "initialization": {"x": -1, "u": -2},
            },
            {
                "id": "math2",
                "path": "MathFMUV3.fmu",
                "initialization": {"x": 20, "u": 1},
            },
        ],
        "connections": {
            ("math1", "y"): [("math2", "x")],
            ("math2", "y"): [("math1", "x")],
        },
        "sequence_order": [["math1", "math2"]],
    }
    master = Master(**correct_config)
    math1_handler = master.fmu_handlers["math1"]

    math1_handler.set_variables({"u": [8]})
    math1_handler.set_variables({"x": [11]})
    outputs = {}
    outputs["0"] = math1_handler.step(0, 1, {})
    outputs["1"] = math1_handler.step(1, 1, {})
    outputs["2"] = math1_handler.step(2, 1, {})
    state = math1_handler.get_state()
    math1_handler.step(3, 1, {})
    math1_handler.set_state(state)
    math1_handler.set_variables({"u": [6]})
    math1_handler.set_variables({"x": [25]})
    outputs["3"] = math1_handler.step(3, 1, {})

    assert outputs == {
        "0": {"y": [17.8]},
        "1": {"y": [17.8]},
        "2": {"y": [17.8]},
        "3": {"y": [27.0]},
    }


def test_bad_fmu_for_cosimulation():
    bad_config = {
        "fmu_config_list": [
            {
                "id": "math2",
                "path": "MathFMUV3Bad.fmu",
                "initialization": {"x": -1, "u": -2},
            }
        ],
        "connections": {},
        "sequence_order": [],
        "iterative": True,
    }

    with pytest.raises(
        Exception,
        match="Can't get or set States on fmu MathFMUV3Bad.fmu but it "
        + "is required for iterative solvers.",
    ):
        master = Master(**bad_config)
