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
Module for handling data streams. This module contains the base class for data stream
handlers and the child classes for different types of data stream handlers.

The data stream handlers are used to read data from different sources, such as CSV
files, Kafka topics, or dictionaries.

The base class `BaseDataStreamHandler` defines the interface for the data stream
handlers. The child classes implement the specific logic to read data from the
different sources.
"""

from .base_data_stream_handler import BaseDataStreamHandler
from .csv_data_stream_handler import CsvDataStreamHandler
from .kafka_data_stream_handler import KafkaDataStreamHandler
from .local_data_stream_handler import LocalDataStreamHandler

# Register all the handlers. This is necessary to be able to create the handlers
# from configuration.
# If a new handler is added, it must be imported here and registered.
list_of_handlers = [
    CsvDataStreamHandler,
    KafkaDataStreamHandler,
    LocalDataStreamHandler,
]

for handler in list_of_handlers:
    BaseDataStreamHandler.register_handler(handler)

__all__ = [
    "BaseDataStreamHandler",
    "CsvDataStreamHandler",
    "KafkaDataStreamHandler",
    "LocalDataStreamHandler",
]
