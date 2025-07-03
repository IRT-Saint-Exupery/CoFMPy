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
from cofmpy.data_stream_handler.csv_data_stream_handler import CsvDataStreamHandler

TEST_DATA_PREVIOUS = [(2, 30), (1.5, 20), (3, 40)]
TEST_DATA_OO_RANGE = [(0, 10), (3.5, 40), (5, 40)]
TEST_DATA_LINEAR = [(1.5, 25), (2.5, 35)]

def get_csv_content():
    """
    Return a mock CSV content as a string.
    """
    return """t,variable
0.5,10
1,20
2,30
3,40
"""

@pytest.fixture
def csv_file(tmp_path):
    """
    Fixture that writes mock CSV data to a temporary file.
    """
    path = tmp_path / "test_data.csv"
    path.write_text(get_csv_content())
    return str(path)

def test_csv_handler_initialization(csv_file):
    handler = CsvDataStreamHandler(csv_file, "variable")
    assert handler.path == csv_file
    assert handler.variable_name == "variable"
    assert handler.interpolator.method == "previous"
    assert not handler.data.empty
    handler = CsvDataStreamHandler(csv_file, "variable", "spline")
    assert handler.interpolator.method == "spline"


def test_get_data_previous_interpolation(csv_file):
    handler = CsvDataStreamHandler(csv_file, "variable")
    for (x_, y_) in TEST_DATA_PREVIOUS:
        interp_y = handler.get_data(x_)
        assert isinstance(interp_y, float)
        assert interp_y == y_


def test_get_data_linear_interpolation(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(get_csv_content())
    handler = CsvDataStreamHandler(str(csv_file), "variable", interpolation="linear")
    for (x_, y_) in TEST_DATA_LINEAR:
        interp_y = handler.get_data(x_)
        assert isinstance(interp_y, float)
        assert interp_y == y_


def test_get_data_out_of_range(csv_file):
    handler = CsvDataStreamHandler(csv_file, "variable", interpolation="previous")
    for (x_, y_) in TEST_DATA_OO_RANGE:
        interp_y = handler.get_data(x_)
        assert isinstance(interp_y, float)
        assert interp_y == y_


def test_invalid_interpolation(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(get_csv_content())
    with pytest.raises(ValueError, match="Unregistered method 'invalid'."):
        CsvDataStreamHandler(str(csv_file), "variable", interpolation="invalid")
