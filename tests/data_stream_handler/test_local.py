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
import logging

import pandas as pd
import pytest

from cofmupy.data_stream_handler import LocalDataStreamHandler

SAMPLE_VALUES = {"1": 10, "2": 20, "3": 30}
VAR_NAME = ("fmu", "variable")
CONFIG = {"values": SAMPLE_VALUES}
EXPECTED_TIMES = [1.0, 2.0, 3.0]
EXPECTED_VALUES = [10.0, 20.0, 30.0]
TEST_CASE = list(zip(EXPECTED_TIMES, EXPECTED_VALUES))


@pytest.fixture
def handler():
    handler = LocalDataStreamHandler(**CONFIG)
    handler.add_variable(VAR_NAME, "")
    return handler


def test_local_initialization(caplog, handler):

    with caplog.at_level(logging.WARNING):
        LocalDataStreamHandler({})
        assert "Given dict is empty, no value will be used" in caplog.text

    assert isinstance(handler.data, pd.DataFrame)
    assert list(handler.data["t"]) == EXPECTED_TIMES
    assert list(handler.data["values"]) == EXPECTED_VALUES


def test_local_add_variable(handler, caplog):
    """Verify that new variables cannot be added."""
    new_var = ("new", "var")
    with pytest.raises(ValueError):
        with caplog.at_level(logging.ERROR):
            handler.add_variable(new_var, "")
            assert "Error: 'add_variable' called" in caplog.text


@pytest.mark.parametrize("timestamp, expected", TEST_CASE)
def test_local_get_data(handler, timestamp, expected):
    """Check data retrieval for exact timestamps."""
    assert handler.get_data(timestamp)[VAR_NAME] == expected


def test_local_empty(caplog):
    """Test that empty config doesn't break handler, but logs warnings."""
    with caplog.at_level(logging.DEBUG):
        LocalDataStreamHandler({})
        assert "Given dict is empty, no value will be used" in caplog.text


def test_is_equivalent_stream(handler, caplog):
    with caplog.at_level(logging.DEBUG):
        res = handler.is_equivalent_stream(**CONFIG)
        assert res == False
        assert "Each handler is unique. Returning False." in caplog.text
