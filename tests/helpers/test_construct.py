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
Unit tests for the construct config helpers scripts.

The tests are based on the following use cases:
    1. source fmu.
    2. resistor fmu

"""
import os
import pytest

from cofmupy.helpers import construct_config
from cofmupy.config_parser import ConfigParser

use_cases = [
    {  # Use case 1: source fmu
        "use_case_name": "source_resistor",
        "connection_path": "../data/connections_source_resistor.csv",
        "initialization_path": "../data/initializations_source_resistor.csv"
    }
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

    Returns:
        tuple: the fmu path, and the expected results.
    """
    current_test_filepath = os.path.dirname(os.path.abspath(__file__))
    connection_path = os.path.join(current_test_filepath, request.param["connection_path"])
    initialization_path = os.path.join(current_test_filepath, request.param["initialization_path"])
    return connection_path, initialization_path


@pytest.fixture
def connection_path(use_case):
    return use_case[0]


@pytest.fixture
def initialization_path(use_case):
    return use_case[1]


def test_construct_config_without_init(connection_path, initialization_path):
    """
    Check construct config file from connections and initializations
    """
    construct_config.construct_config(connection_path, None)
    assert os.path.isfile("./config.json")

    parser = ConfigParser("./config.json")
    assert len(parser.config_dict["fmus"]) == 2
    assert len(parser.config_dict["connections"]) == 1


def test_construct_config(connection_path, initialization_path):
    """
    Check construct config file from connections and initializations
    """
    construct_config.construct_config(connection_path, initialization_path)
    assert os.path.isfile(f"./config.json")

    parser = ConfigParser("./config.json")
    assert len(parser.config_dict["fmus"]) == 2
    assert len(parser.config_dict["connections"]) == 1

    assert len(parser.config_dict["fmus"][0]["initialization"].keys()) == 0
    assert len(parser.config_dict["fmus"][1]["initialization"].keys()) == 1
