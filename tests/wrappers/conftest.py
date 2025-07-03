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
import pytest
import os
from fmpy.model_description import ModelDescription
from fmpy.fmi2 import FMU2Slave, FMICallException
from fmpy.fmi3 import FMU3Slave
from cofmpy.wrappers import FmuHandlerFactory, Fmu2Handler, Fmu3Handler

description_keys = [
    "fmiVersion", "modelName", "guid", "description", "author", "version",
    "copyright", "license", "generationTool", "generationDateAndTime",
    "variableNamingConvention", "numberOfContinuousStates", "numberOfEventIndicators",
    "defaultExperiment", "coSimulation", "modelExchange", "scheduledExecution",
    "buildConfigurations", "unitDefinitions", "typeDefinitions", "modelVariables",
    "outputs", "derivatives", "clockedStates", "eventIndicators", "initialUnknowns"
]
factory_class = FmuHandlerFactory
description_class = ModelDescription
float_precision = 2
nb_steps = 5
current_time = 0.0

DIR = "tests/wrappers/assets"
fmu_2_path = os.path.join(DIR, "TimeFMU2.fmu")
fmu_3_path = os.path.join(DIR, "BouncingBall.fmu")

PARAMS_DICT = {
    fmu_2_path: lambda: {
        "version": "2.0",
        "handler": Fmu2Handler,
        "slave": FMU2Slave,
        "factory": (factory := FmuHandlerFactory(fmu_2_path)),
        "fmu": (fmu := factory()),
        "default_step": None,
        "variables": {
            "in": ["input_real"],
            "out": ["output_real"],
            "par": ["fixed_param", "string_var"],
        },
        "exception": FMICallException,
        "err_msg_cancel": "fmi2CancelStep failed with status 3 (error).",
        "err_msg_get": "",
        "err_msg_set_state": "",
        "err_msg_set_var": "",
        "step_size": 1,
        "input_dict": {"input_real": [1.0]},
        "expected_results": [46.0, -51.0],
        "expected_get_var": {
            "input_real": [1.0], "output_real": [0.0],
            "fixed_param": [42], "string_var": [b"Hello"],
        },
        "expected_get_causality": ["input", "output", "parameter", "parameter"],
        "expected_var_types": ["Real", "Real", "Integer", "String"],
    },
    fmu_3_path: lambda: {
        "version": "3.0",
        "handler": Fmu3Handler,
        "slave": FMU3Slave,
        "factory": (factory := FmuHandlerFactory(fmu_3_path)),
        "fmu": (fmu := factory()),
        "default_step": 0.01,
        "variables": {
            "in": [],
            "out": ["h", "v"],
            "par": ["time", "der(h)", "der(v)", "g", "e", "v_min"],
        },
        "exception": AttributeError,
        "err_msg_cancel": "'FMU3Slave' object has no attribute 'cancelStep'",
        "err_msg_get": "'FMU3Slave' object has no attribute 'getFMUstate'",
        "err_msg_set_state": "'FMU3Slave' object has no attribute 'setFMUstate'",
        "err_msg_set_var": "Variable type Float64 not supported",
        "step_size": 0.1,
        "input_dict": {"h": [1.0], "v": [0.0]},
        "expected_results": [0.14, 2.65],
        "expected_get_var": {
            "h": [1.0], "v": [0.0], "time": [0.0], "der(h)": [0.0],
            "der(v)": [-9.81], "g": [-9.81], "e": [0.7], "v_min": [0.1],
        },
        "expected_get_causality": [
            "independent", "output", "local", "output", "local", "parameter",
            "parameter", "local",
        ],
        "expected_var_types": ["Float64"] * 8,
    },
}


@pytest.fixture
def wrapper_params(request):
    """Fixture to instantiate FMU based on the requested path."""
    return PARAMS_DICT[request.param]()


def do_step(fmu, num_steps, current_t, stepsize, in_dict):
    """Performs a step"""

    for _ in range(num_steps):
        outputs = fmu.step(current_t, stepsize, in_dict)
        current_t += stepsize

    return outputs, current_t, in_dict
