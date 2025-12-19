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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Storage handler module :
- Store available data storage
- notify data storage on results events
"""
from .base_data_storage import BaseDataStorage


class StorageHandler:
    """
    Manages Storage handlers :
        - Store available data storage
        - notify data storage on results events
    Attributes:
        _storage (list): List of available storages

    """

    def __init__(self):
        """
        Initializes the StorageHandler class
        """
        self._storage: list[BaseDataStorage] = []

    def register_storage(self, type_storage: str, config: dict) -> None:
        """
        Register given storage as an available data storage

        Args:
            type_storage (str): type of the storage, should be used to filter events.
            config (dict): config of the data storage, specific to storage type
        """
        data_storage = BaseDataStorage.create_data_storage(
            {"type": type_storage, "config": config}
        )
        self._storage.append(data_storage)

    def notify_results(
        self, type_storage: str, time: float, data, metadata=None
    ) -> None:
        """
        Notify results to concerned data storage

        Args:
            type_storage (str): type of the storage, should be used to filter events.
            time (float): time of the results
            data (any): data to send
            metadata (any) : optional data to send
        """
        for storage in self._storage:
            if storage.type_name == type_storage:
                storage.save(time, data, metadata)
