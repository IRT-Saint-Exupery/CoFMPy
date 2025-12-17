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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Unit tests for the extract helpers scripts.

The tests are based on the following use cases:
    1. source fmu.
    2. resistor fmu

"""
import os
import pytest

from cofmupy.helpers import extract_fmu
from cofmupy.utils import fmu_utils

use_cases = [
    {  # Use case 1: source fmu
        "use_case_name": "source",
        "path": "../../resources/fmus/source.fmu",
        "expected_results": [
            {'name': 'amplitude', 'type': 'Fixed', 'start': '20', 'category': 'Parameter'},
            {'name': 'frequency', 'type': 'Fixed', 'start': '1', 'category': 'Parameter'},
            {'name': 'phase', 'type': 'Fixed', 'start': '0', 'category': 'Parameter'},
            {'name': 'V', 'type': 'Continuous', 'start': '-', 'category': 'Output'}
        ],
    },
    {  # Use case 2: resistor fmu
       # jacobi algo
        "use_case_name": "resistor",
        "path": "../../resources/fmus/resistor.fmu",
        "expected_results": [
            {'name': 'I', 'type': 'Continuous', 'start': '-', 'category': 'Output'},
            {'name': 'V', 'type': 'Continuous', 'start': '20', 'category': 'Input'},
            {'name': 'R', 'type': 'Fixed', 'start': '1', 'category': 'Parameter'}
        ],
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
    - the fmu path.
    - the expected results (dictionary)
    - the use case name

    Returns:
        tuple: the fmu path, the expected results and use case name
    """
    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_test_filepath, request.param["path"])
    return path, request.param["expected_results"], request.param["use_case_name"]


@pytest.fixture
def path(use_case):
    return use_case[0]


@pytest.fixture
def expected_results(use_case):
    return use_case[1]


@pytest.fixture
def use_case_name(use_case):
    return use_case[2]


def test_display_information(path, expected_results, use_case_name):
    """
    Check display fmu information method works without any exception
    """
    try:
        extract_fmu.display_fmu_info(path)
    except Exception:
        pytest.fail("An exception was raised unexpectedly")


def test_retrieve_information(path, expected_results, use_case_name):
    """
    Check display fmu information method works without any exception
    """

    fmu_information = fmu_utils.retrieve_fmu_info(path)
    assert fmu_information == expected_results


def test_export_information(path, expected_results, use_case_name):
    """
    Check export fmu information method works by checking exported file exist
    """

    extract_fmu.export_fmu_info(path, f"./{use_case_name}.csv")
    assert os.path.isfile(f"./{use_case_name}.csv")
