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
File data storage module.

This module contains the class to save data to CSV files.
"""

import os

import pandas as pd

from .base_data_storage import BaseDataStorage


class FileDataStorage(BaseDataStorage):
    """Data storage to save data to files."""

    type_name = "file"

    def __init__(self, output_dir, overwrite=True):
        self.output_dir = output_dir

        # Raise error if directory already exists and overwrite is False
        if overwrite is False:
            if os.path.exists(output_dir):
                raise FileExistsError(f"Directory {output_dir} already exists.")

        # Create directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Empty directory
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))

    def save(self, variable_name, data, metadata=None):
        """Save data to a file for the given variable.

        The data must be a list of lists, where each list contains the data for a row
        (time t, value at t).

        Args:
            variable_name (str): variable name.
            data (list): list of lists with the data to save
            metadata (dict, optional): metadata associated with the data.
        """
        with open(self._file_path(variable_name), mode="a", encoding="utf-8") as f:
            for d in data:
                f.write(",".join(map(str, d)) + "\n")

    def load(self, variable_name):
        """Load data from a file for the given variable.

        Args:
            variable_name (str): variable name.

        Returns:
            pd.DataFrame: loaded data.
        """
        return pd.read_csv(self._file_path(variable_name), header="infer")

    def delete(self, variable_name):
        os.remove(self._file_path(variable_name))

    def _file_path(self, variable_name):
        return os.path.join(self.output_dir, f"{variable_name}.csv")
