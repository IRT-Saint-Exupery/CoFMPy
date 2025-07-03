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
"""
This module contains the child class for CSV data stream handler.
"""

import pandas as pd

from .base_data_stream_handler import BaseDataStreamHandler
from ..utils import Interpolator


class CsvDataStreamHandler(BaseDataStreamHandler):
    """
    Child class for CSV data stream handler.
    """

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "csv"

    def __init__(self, path, variable, interpolation="previous"):
        """
        Constructor for CSV data stream handler.

        Args:
            path (str): path to the CSV file.
            variable (str): name of the variable to extract from the CSV file.
            interpolation (str): type of interpolation to use when data is requested at
                a timestamp other than available data values. The extrapolation behaviour
                depends on the chosen method: see cofmpy.utils.Interpolator.
                Available methods are given by `Interpolator()._registry.keys()`.
                Usually: 'linear', 'cubic', 'quadratic', 'previous', 'nearest', 'spline'.
                Defaults to 'previous.
        """
        self.path = path
        self.variable_name = variable

        self.interpolator = Interpolator(interpolation)
        self.data = pd.read_csv(path)
        self.data = self.data[["t", self.variable_name]]

    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            float: data value at the requested time.
        """
        return self.interpolator(self.data["t"], self.data[self.variable_name], [t])[0]
