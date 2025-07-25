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
import os
import pytest
import pandas as pd
from cofmpy.coordinator import Coordinator

@pytest.fixture(scope="module", autouse=True)
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

from cofmpy.coordinator import Coordinator


def test_literal_data_stream_handler_integration(literal_two_resistors_test):

    config, expected_results = literal_two_resistors_test
    coordinator = Coordinator()
    coordinator.start(config)
    for _ in range(80):
        coordinator.do_step(0.05)

    results = pd.DataFrame(coordinator.get_results())
    results = results.set_index("time")

    assert results.to_dict() == expected_results
