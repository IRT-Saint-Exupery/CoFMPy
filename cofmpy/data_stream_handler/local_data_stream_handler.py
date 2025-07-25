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
This module contains the child class for Values data stream handler.
"""
import logging

import pandas as pd

from ..utils import Interpolator
from .base_data_stream_handler import BaseDataStreamHandler

logger = logging.getLogger(__name__)


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

    def __init__(self, config):
        super().__init__()

        if "values" not in config:
            logger.error(f"'values' not found in 'config'. Handler: ({self})")
        if "interpolation" not in config:
            logger.info("Interpolation method not provided, using default 'previous'.")

        self.values = config.get("values", {})
        self.interpolator = Interpolator(config.get("interpolation", "previous"))

        list_t = [float(t) for t in self.values]
        list_values = [float(val) for val in self.values.values()]
        self.data = pd.DataFrame.from_dict({"t": list_t, "values": list_values})

    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            float: data at the requested time.
        """
        out_dict = {}
        for (node, endpoint), _ in self.alias_mapping.items():
            out_dict[(node, endpoint)] = self.interpolator(
                self.data["t"], self.data["values"], [t]
            )[0]

        return out_dict

    def is_equivalent_stream(self, config: dict) -> bool:
        """
        Check if the current data stream handler instance is equivalent to
        another that would be created with the given config.
        This local data handler is always considered as unique.

        Args:
            config (dict): config for the data stream handler to compare.

        Returns:
            bool: True if the handlers are equivalent, False otherwise.
        """
        logger.debug(f"Not used (each handler is unique): {config}")

        return False

    def add_variable(self, endpoint: tuple, stream_alias: str):
        """
        Add a new variable to the data stream handler.

        Args:
            endpoint (tuple): key of the variable to add in the format:
                (node_name, endpoint_name).
            stream_alias (str): not used since values are passed direcly
                in config under 'values' key.
        """
        logger.debug(f"Argument not used: {stream_alias}")
        self.alias_mapping.update({endpoint: "values"})
