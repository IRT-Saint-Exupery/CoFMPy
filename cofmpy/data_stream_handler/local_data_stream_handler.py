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
    This data stream handler receives the values of the
    variable directly from the JSON main configuration file.

    Each LocalDataStreamHandler instance is associated to a single variable.
    As a consequence:
    * `is_equivalent_stream` method always returns False
    * `add_variable` is overriden so `alias_mapping` use is replaced
        by using its single key.

    Args:
        values (dict): dictionary with the values to process
            in the format {'t1':value1, ...}
    """

    # Type name of the handler (used in the configuration file and handler registration)
    type_name = "literal"

    def __init__(self, values, interpolation="previous"):
        if not values:
            logger.warning("Given dict is empty, no value will be used")
        super().__init__()
        self.single_key = None
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
            dict: for the requested time, returns dict of values associated to variables
                under the data handler scope (see BaseDataStreamHandler.is_equivalent_stream).
                Format : {(fmu_i, var_j): value_1, (fmu_k, var_l): value_2}, ...}
        """
        out_dict = {
            self.single_key: self.interpolator(
                self.data["t"], self.data["values"], [t]
            )[0]
        }

        return out_dict

    # pylint: disable=W0237
    def is_equivalent_stream(self, values, interpolation="previous") -> bool:
        """
        Check if the current data stream handler instance is equivalent to
        another that would be created with the given config.
        This local data handler is always considered as unique.

        Args:
            The constructor is exacly the same than in __init__.

        Returns:
            bool: True if the handlers are equivalent, False otherwise.
        """
        _ = values, interpolation
        logger.debug("Each handler is unique. Returning False.")

        return False

    def add_variable(self, variable: tuple, stream_alias: str):
        """Extracts the single key in alias_mapping"""
        if len(self.alias_mapping) == 1:
            err_msg = (
                "Error: 'add_variable' called while alias_mappping "
                "already contains one variable. "
                "This is not allowed for the current LocalDataStreamHandler."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        logger.debug(f"Argument not used: {stream_alias}")
        self.alias_mapping.update({variable: stream_alias})
        logger.debug(
            f"single_key ({self.single_key}) will be used "
            f"instead of alias_mapping ({self.alias_mapping})"
        )
        self.single_key = variable
