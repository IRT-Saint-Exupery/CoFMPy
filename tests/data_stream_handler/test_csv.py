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
import logging
import pytest

from cofmpy.data_stream_handler.csv_data_stream_handler import CsvDataStreamHandler

# === Test Data ===

TEST_DATA_PREVIOUS = [(1.3, 10), (1.5, 10), (2.9, 1.2)]
TEST_DATA_OUT_OF_RANGE = [(-1, 0.5), (3.5, 1.2), (5, 1.2)]
TEST_DATA_LINEAR = [(1.5, 8.9), (2.4, 3.95)]


# === Fixtures ===


@pytest.fixture
def csv_config(generate_csv):
    """Returns a CSV config dictionary using the first generated CSV file."""
    return {
        "path": generate_csv[0],
        "variable": "variable",
    }

@pytest.fixture
def csv_handler_init(csv_config):
    """Initializes a CsvDataStreamHandler with default 'previous' interpolation."""
    handler = CsvDataStreamHandler(csv_config)
    var_name = ("node", "endpoint")
    handler.add_variable(var_name, "variable")
    return handler, var_name


# === Tests ===

def test_csv_handler_initialization(csv_config):
    """Check CSV handler setup with default and custom interpolation methods."""
    handler = CsvDataStreamHandler(csv_config)
    assert handler.path == csv_config["path"]
    assert handler.interpolator.method == "previous"
    assert not handler.data.empty

    csv_config["interpolation"] = "spline"
    handler = CsvDataStreamHandler(csv_config)
    assert handler.interpolator.method == "spline"


@pytest.mark.parametrize("x_input, expected", TEST_DATA_PREVIOUS)
def test_get_data_previous_interpolation(csv_handler_init, x_input, expected):
    """Verify 'previous' interpolation returns correct results."""
    handler, var_name = csv_handler_init
    result = handler.get_data(x_input)[var_name]
    assert isinstance(result, float)
    assert result == expected


@pytest.mark.parametrize("x_input, expected", TEST_DATA_LINEAR)
def test_get_data_linear_interpolation(csv_handler_init, x_input, expected):
    """Verify 'linear' interpolation returns correct interpolated values."""
    handler, var_name = csv_handler_init
    handler.interpolator.method = "linear"
    result = handler.get_data(x_input)[var_name]
    assert isinstance(result, float)
    assert result == expected


@pytest.mark.parametrize("x_input, expected", TEST_DATA_OUT_OF_RANGE)
def test_get_data_out_of_range(csv_handler_init, x_input, expected):
    """Test data points outside the provided time range (extrapolation or boundary)."""
    handler, var_name = csv_handler_init
    result = handler.get_data(x_input)[var_name]
    assert isinstance(result, float)
    assert result == expected


def test_invalid_interpolation(csv_config):
    """Ensure unsupported interpolation methods raise a ValueError."""
    csv_config["interpolation"] = "invalid"
    with pytest.raises(ValueError, match="Unregistered method 'invalid'."):
        CsvDataStreamHandler(csv_config)

def test_csv_empty(caplog):
    """Test that empty config doesn't break handler, but logs warnings."""
    with caplog.at_level(logging.DEBUG):
        CsvDataStreamHandler({})
        assert "'path' not found in 'config'." in caplog.text 
        assert "Interpolation method not provided, using default" in caplog.text
        assert "Failed to initialize:" in caplog.text
