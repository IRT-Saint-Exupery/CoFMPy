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
"""
This module contains the child class for CSV data stream handler.
"""

import logging

import pandas as pd

from ..utils import Interpolator
from .base_data_stream_handler import BaseDataStreamHandler

logger = logging.getLogger(__name__)


class CsvDataStreamHandler(BaseDataStreamHandler):
    """
    Child class for CSV data stream handler.
    """

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "csv"

    # def __init__(self, path, variable, interpolation="previous"):
    def __init__(self, config):
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
        super().__init__()

        if "path" not in config:
            logger.error(f"'path' not found in 'config'. Handler: ({self})")
        if "interpolation" not in config:
            logger.info("Interpolation method not provided, using default 'previous'.")

        self.path = config.get("path")
        self.interpolator = Interpolator(config.get("interpolation", "previous"))

        if self.path:
            self.data = pd.read_csv(self.path)
        else:
            logger.error(f"Failed to initialize: {self}")

    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            dict: for the requested time, returns dict of values associated to endpoints
                under the data handler scope (see BaseDataStreamHandler.is_equivalent_stream).
                Format : {(fmu_i, var_j): value_1, (fmu_k, var_l): value_2}, ...}
        """
        out_dict = {}
        for (node, endpoint), stream_alias in self.alias_mapping.items():
            out_dict[(node, endpoint)] = self.interpolator(
                self.data["t"], self.data[stream_alias], [t]
            )[0]

        return out_dict

    def is_equivalent_stream(self, config: dict) -> bool:
        """
        Check if the current data stream handler instance is equivalent to
        another that would be created with the given config.
        This csv data handler groups all variables present in one same csv into one
        handler instance.

        Args:
            config (dict): config for the data stream handler to compare.

        Returns:
            bool: True if the handlers are equivalent, False otherwise.
        """

        # equivalence item: csv path (self.path)
        return config["config"]["path"] == self.path
