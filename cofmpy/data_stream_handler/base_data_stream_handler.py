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
This module contains the base class for data stream handlers.
"""

from abc import abstractmethod


class BaseDataStreamHandler:
    """
    Base class for data stream handlers.
    """

    # Type name of the handler (used in the configuration file)
    type_name = None

    # Registry of available handlers
    _handlers_registry = {}

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    def register_handler(cls, subclass):
        """Register a subclass handler in the registry.

        The subclass must inherit from BaseDataStreamHandler and have a `type_name`
        class attribute. The `type_name` attribute is used to identify the handler
        type in the configuration file.

        Args:
            subclass (BaseDataStreamHandler): data stream handler subclass to register.
        """
        if not issubclass(subclass, BaseDataStreamHandler):
            raise TypeError(f"Class {subclass.__name__} must inherit from BaseClass.")
        key = subclass.type_name
        cls._handlers_registry[key] = subclass

    @classmethod
    def create_handler(cls, config_dict):
        """Factory method to create a class instance based on config_dict.

        The config_dict must contain a `type` key that corresponds to the `type_name`
        class attribute of the handler subclass. The config_dict also contains a config
        dictionary that is passed to the handler constructor.

        Args:
            config_dict (dict): configuration dictionary. Must contain a `type` key and
                a `config` key to initialize the handler.

        Returns:
            BaseDataStreamHandler: a new data stream handler instance.
        """
        handler_type = config_dict.get("type")
        if handler_type not in cls._handlers_registry:
            raise ValueError(
                f"Unknown handler type '{handler_type}'."
                f"Available types: {list(cls._handlers_registry.keys())}"
            )
        return cls._handlers_registry[handler_type](**config_dict["config"])

    @abstractmethod
    def get_data(self, t: float):
        """
        Get the data at a specific time.

        Args:
            t (float): timestamp to get the data.

        Returns:
            pd.Series: data at the requested time.
        """
