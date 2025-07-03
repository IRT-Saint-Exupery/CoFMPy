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
import pandas as pd
import logging
from cofmpy.data_stream_handler.local_data_stream_handler import LocalDataStreamHandler


def test_local_data_stream_handler_initialization():
    values = {"1": 10, "2": 20, "3": 30}
    handler = LocalDataStreamHandler(values)

    assert isinstance(handler.data, pd.DataFrame)
    assert list(handler.data["t"]) == [1.0, 2.0, 3.0]
    assert list(handler.data["values"]) == [10.0, 20.0, 30.0]


def test_local_data_stream_handler_get_data():
    values = {"1": 10, "2": 20, "3": 30}
    handler = LocalDataStreamHandler(values)

    assert handler.get_data(1.5) == 10.0
    assert handler.get_data(2.5) == 20.0
    assert handler.get_data(3.0) == 30.0


@pytest.mark.skip(reason="Skipping this test until the coordinator handles the return")
def test_local_data_stream_handler_get_data_before_range(caplog):
    values = {"1": 10, "2": 20, "3": 30}
    handler = LocalDataStreamHandler(values)
    with caplog.at_level(logging.WARNING):
        handler.get_data(0.5)
        assert (
            "Timestamp 0.5 is before available data range. Default variable value will be used instead"
            in caplog.text
        )


def test_local_data_stream_handler_get_data_after_range():
    values = {"1": 10, "2": 20, "3": 30}
    handler = LocalDataStreamHandler(values)
    assert handler.get_data(10.0) == 30.0  # Should return the last available value


def test_local_data_stream_handler_empty(caplog):
    # Test with empty dictionary
    with caplog.at_level(logging.WARNING):
        LocalDataStreamHandler({})  # Should not raise an error
        assert "Given dict is empty, no value will be used" in caplog.text
