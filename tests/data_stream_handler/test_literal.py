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
import pytest
import pandas as pd
import logging
from cofmpy.data_stream_handler.local_data_stream_handler import LocalDataStreamHandler

# === Constants ===

SAMPLE_VALUES = {"1": 10, "2": 20, "3": 30}
VAR_NAME = ("node", "endpoint")

EXPECTED_TIMES = [1.0, 2.0, 3.0]
EXPECTED_VALUES = [10.0, 20.0, 30.0]
INTERPOLATED_TESTS = [(1.5, 10), (2.5, 20)]
OUT_OF_RANGE_AFTER = [(4.0, 30), (10.0, 30)]
IN_RANGE_TESTS = list(zip(EXPECTED_TIMES, EXPECTED_VALUES))


# === Fixtures ===

@pytest.fixture(scope="function")
def literal_handler():
    """Initializes a LocalDataStreamHandler with sample literal values."""
    config = {"values": SAMPLE_VALUES}
    handler = LocalDataStreamHandler(config)
    handler.add_variable(VAR_NAME, "")
    return handler


# === Tests ===

def test_literal_initialization(literal_handler):
    """Check initialization: data structure, column content, and value types."""
    handler = literal_handler

    assert isinstance(handler.data, pd.DataFrame)
    assert VAR_NAME in handler.alias_mapping
    assert list(handler.data["t"]) == EXPECTED_TIMES
    assert list(handler.data["values"]) == EXPECTED_VALUES


def test_local_add_variable(literal_handler):
    """Verify that new variables can be added and tracked."""
    handler = literal_handler
    new_var = ("new", "var")
    handler.add_variable(new_var, "")
    assert new_var in handler.alias_mapping


@pytest.mark.parametrize("timestamp, expected", IN_RANGE_TESTS)
def test_local_get_data(literal_handler, timestamp, expected):
    """Check data retrieval for exact timestamps."""
    handler = literal_handler
    assert handler.get_data(timestamp)[VAR_NAME] == expected


@pytest.mark.parametrize("timestamp, expected", INTERPOLATED_TESTS)
def test_local_get_interp_data(literal_handler, timestamp, expected):
    """Verify that data is interpolated with 'previous' strategy by default."""
    handler = literal_handler
    assert handler.get_data(timestamp)[VAR_NAME] == expected


@pytest.mark.parametrize("timestamp, expected", OUT_OF_RANGE_AFTER)
def test_local_get_data_after_range(literal_handler, timestamp, expected):
    """Ensure values after data range return the last available value."""
    handler = literal_handler
    assert handler.get_data(timestamp)[VAR_NAME] == expected


@pytest.mark.skip(reason="Coordinator does not yet handle this behavior.")
def test_local_get_data_before_range(caplog, literal_handler):
    """Check if a warning is raised for timestamps before data starts."""
    handler = literal_handler
    with caplog.at_level(logging.WARNING):
        handler.get_data(0.5)
        assert (
            "Timestamp 0.5 is before available data range. Default variable value will be used instead"
            in caplog.text
        )


def test_local_empty(caplog):
    """Test that empty config doesn't break handler, but logs warnings."""
    with caplog.at_level(logging.DEBUG):
        LocalDataStreamHandler({})
        assert "'values' not found in 'config'" in caplog.text
        assert "Interpolation method not provided, using default" in caplog.text

