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
This module contains the child class for Values data stream handler.
"""

import pandas as pd
import logging

from .base_data_stream_handler import BaseDataStreamHandler
from ..utils import Interpolator


class LocalDataStreamHandler(BaseDataStreamHandler):
    """
    Data stream handler to read values from a dictionary.

    This data stream handler is the simplest one, as it just reads the values of the
    variable directly from the JSON main configuration file.

    Args:
        values (dict): dictionary with the values to process
    """

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "literal"

    def __init__(self, values, interpolation="previous"):
        if not values:
            logging.warning("Given dict is empty, no value will be used")

        self.values = values
        self.interpolator = Interpolator(interpolation)

        list_t = [float(t) for t in values]
        list_values = [float(val) for val in values.values()]
        self.data = pd.DataFrame.from_dict({"t": list_t, "values": list_values})

    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            float: data at the requested time.
        """
        if t < self.data["t"].values[0]:
            logging.warning(
                f"Timestamp {t} is before available data range. "
                "Extrapolated variable value will be used instead"
            )
        return self.interpolator(self.data["t"], self.data["values"], [t])[0]
