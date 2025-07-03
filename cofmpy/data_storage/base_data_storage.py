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
Base class for data storages.
"""

from abc import ABC, abstractmethod


class BaseDataStorage(ABC):
    """
    Base class for data storages.

    Data storages are used to save and load data. The data storage can be a file, a
    database, a cloud storage, etc. Each data storage subclass must implement the
    `save`, `load`, and `delete` methods.

    The data storage is initialized with a configuration dictionary that contains the
    necessary parameters to connect to the storage. The configuration dictionary must
    contain a `type` key that corresponds to the `type_name` class attribute of the data
    storage subclass. The configuration dictionary also contains a `config` key with the
    parameters to initialize the data storage.

    The data storage class also contains a registry of available data storages. The
    subclasses must be registered in the registry using the `register_data_storage`
    class method.
    """

    # Type name of the data storage (used in the configuration file)
    type_name = None

    # Registry of available data storages
    _data_storages_registry = {}

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    def register_data_storage(cls, subclass):
        """Register a subclass data storage in the registry.

        The subclass must inherit from BaseDataStorage and have a `type_name`
        class attribute. The `type_name` attribute is used to identify the data storage
        type in the configuration file.

        Args:
            subclass (BaseDataStorage): data storage subclass to register.
        """
        if not issubclass(subclass, BaseDataStorage):
            raise TypeError(f"Class {subclass.__name__} must inherit from BaseClass.")
        key = subclass.type_name
        cls._data_storages_registry[key] = subclass

    @classmethod
    def create_data_storage(cls, config_dict):
        """Factory method to create a class instance based on config_dict.

        The config_dict must contain a `type` key that corresponds to the `type_name`
        class attribute of the data storage subclass. The config_dict also contains a config
        dictionary that is passed to the data storage constructor.

        Args:
            config_dict (dict): configuration dictionary. Must contain a `type` key and
                a `config` key to initialize the data storage.

        Returns:
            BaseDataStorage: a new data storage instance.
        """
        storage_type = config_dict.get("type")
        if storage_type not in cls._data_storages_registry:
            raise ValueError(
                f"Unknown data storage type '{storage_type}'."
                f"Available types: {list(cls._data_storages_registry.keys())}"
            )
        return cls._data_storages_registry[storage_type](**config_dict["config"])

    @abstractmethod
    def save(self, variable_name, data, metadata=None):
        """Save data to the storage.

        Args:
            variable_name (str): variable name.
            data (any): data to save.
            metadata (dict, optional): metadata associated with the data.
        """

    @abstractmethod
    def load(self, variable_name):
        """Load data from the storage.

        Args:
            variable_name (str): variable name.

        Returns:
            any: loaded data.
        """

    @abstractmethod
    def delete(self, variable_name):
        """Delete data from the storage.

        Args:
            variable_name (str): variable name.
        """
