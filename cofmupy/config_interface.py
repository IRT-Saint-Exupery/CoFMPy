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
Interface objects for config parser
"""
from typing import Union
from typing import Dict
from collections import defaultdict

FMU_TYPE = "fmu"
CSV_TYPE = "csv"
LITERAL_TYPE = "literal"


class ConfigConnectionBase:
    """
    Base Connection object definition
    """

    type: str = FMU_TYPE  # default type for connection is "fmu"


class ConfigConnectionFmu(ConfigConnectionBase):
    """
    Fmu Connection extremity object
    """

    id: str
    variable: str
    unit: str

    # pylint: disable=W0622
    def __init__(
        self, id: str, variable: str, unit: str = "", type: str = FMU_TYPE, **kwargs
    ):
        """
        Init method to instantiate Fmu connection extremity
        Args:
            id (str): FMU id
            variable (str): FMU variable name
            unit (str): Unit of the variable
            type (str): Type of the extremity, default to FMU_TYPE
            kwargs (any): additional arguments, not used
        """
        self.type = type
        self.id = id
        self.variable = variable
        self.unit = unit

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {
            "type": self.type,
            "id": self.id,
            "variable": self.variable,
            "unit": self.unit,
        }


class ConfigConnectionLocalStream(ConfigConnectionBase):
    """
    Local stream Connection extremity object
    """

    values: Dict
    interpolation: str
    variable: str = ""

    # pylint: disable=W0622
    def __init__(self, values: Dict, type: str, interpolation="previous", **kwargs):
        """
        Init method to instantiate connection extremity
        Args:
            type (str): Type of the extremity
            values (dict): Managed values
            interpolation (str): Interpolation algorithm name
            kwargs (any): additional arguments, not used
        """
        self.type = type
        self.values = values
        self.interpolation = interpolation

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {
            "type": self.type,
            "values": self.values,
            "variable": self.variable,
            "interpolation": self.interpolation,
        }


class ConfigConnectionCsvStream(ConfigConnectionBase):
    """
    Csv stream Connection extremity object
    """

    path: str
    variable: str = ""
    interpolation: str

    # pylint: disable=W0622
    def __init__(
        self, path: str, variable: str, type: str, interpolation="previous", **kwargs
    ):
        """
        Init method to instantiate connection extremity
        Args:
            type (str): Type of the extremity
            path (str): csv file path
            variable (str): concerned variable name into csv
            interpolation (str): Interpolation algorithm name
            kwargs (any): additional arguments, not used
        """
        self.type = type
        self.path = path
        self.variable = variable
        self.interpolation = interpolation

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {
            "type": self.type,
            "path": self.path,
            "variable": self.variable,
            "interpolation": self.interpolation,
        }


class ConfigConnectionStorage(ConfigConnectionBase):
    """
    Data storage Connection extremity object
    """

    id: str
    variable: str = ""
    alias: str

    # pylint: disable=W0622
    def __init__(self, id: str, alias: str, type: str, **kwargs):
        """
        Init method to instantiate connection extremity
        Args:
            id (str): id of tha data storage to use, linked to the name
            alias (str): title expected into the storage
            type (str): Type of the extremity
            kwargs (any): additional arguments, not used
        """
        self.type = type
        self.id = id
        self.alias = alias

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {
            "type": self.type,
            "id": self.id,
            "variable": self.variable,
            "alias": self.alias,
        }


class ConfigDataStorage:
    """
    Data storage object, should be a file, a database, a stream, ...
    """

    name: str
    type: str
    config: Dict

    # pylint: disable=W0622
    def __init__(self, name: str, config: Dict, type: str, **kwargs):
        """
        Init method to instantiate data storage
        Args:
            name (str): name of the data storage
            type (str): Type of the data storage
            config (dict): specific config for this data storage
            kwargs (any): additional arguments, not used
        """
        self.name = name
        self.type = type
        self.config = config

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {"name": self.name, "type": self.type, "config": self.config}


class ConfigConnection:
    """
    Connection object, composed of 2 extremity
    """

    source: Union[
        ConfigConnectionFmu, ConfigConnectionLocalStream, ConfigConnectionCsvStream
    ]
    target: list[Union[ConfigConnectionFmu, ConfigConnectionStorage]] = []

    def __init__(self, source: Dict, target: list[Dict], **kwargs):
        """
        Init method to instantiate connection. This initialization accept
            old target format (dict) and new target format (list of dict)
        Args:
            source (dict): connection source object
            target (list[Dict] or dict): List of connection target objects
            kwargs (any): additional arguments, not used
        """
        if "type" in source.keys():
            if source["type"] == FMU_TYPE:
                self.source = ConfigConnectionFmu(**source)
            elif source["type"] == CSV_TYPE:
                self.source = ConfigConnectionCsvStream(**source)
            elif source["type"] == LITERAL_TYPE:
                self.source = ConfigConnectionLocalStream(**source)

            if not isinstance(target, list):
                # TODO : Manage error on config format
                print("target is not a list")
                target = [target]
        else:
            self.source = ConfigConnectionFmu(**source)

        self.target = []
        # Check if target is a dict
        if isinstance(target, dict):
            if "type" in target.keys() and target["type"] != FMU_TYPE:
                self.target.append(ConfigConnectionStorage(**target))
            else:
                self.target.append(ConfigConnectionFmu(**target))
        # else, it's normally a list
        else:
            for target_dict in target:
                if "type" in target_dict.keys() and target_dict["type"] != FMU_TYPE:
                    self.target.append(ConfigConnectionStorage(**target_dict))
                else:
                    self.target.append(ConfigConnectionFmu(**target_dict))

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")


class ConfigFmu:
    """
    Fmu object
    """

    id: str
    name: str
    path: str
    initialization: Dict = {}

    # pylint: disable=W0622
    def __init__(
        self,
        id: str,
        path: str,
        name: str = "",
        initialization: dict = None,
        **kwargs,
    ):
        """
        Init method to instantiate fmu.
        Args:
            id (str): fmu id
            path (str): fmu file name, relative or absolute
            name (str): fmu name (display)
            initialization (dict): variable initializations for the fmu
            kwargs (any): additional arguments, not used
        """
        self.id = id
        self.name = name
        if name == "":
            self.name = id
        self.path = path
        if initialization is None:
            initialization = {}
        self.initialization = initialization

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "initialization": self.initialization,
        }


class ConfigObject:
    """
    Global config object, composed of different object defined above
    """

    root: str
    edge_sep: str
    cosim_method: str
    iterative: bool
    fmus: list[ConfigFmu] = defaultdict(list)
    connections: list[ConfigConnection] = defaultdict(list)
    data_storages: list[ConfigDataStorage] = defaultdict(list)

    def __init__(
        self,
        fmus: list[ConfigFmu],
        connections: list[ConfigConnection] = None,
        data_storages: list[ConfigDataStorage] = None,
        root: str = "",
        edge_sep: str = " -> ",
        cosim_method: str = "jacobi",
        iterative: bool = False,
        **kwargs,
    ):
        """
        Init method to instantiate global config object.
        Args:
            fmus (list): fmus list
            connections (list): connections list
            data_storages (list): data storages list
            root (str): --
            edge_sep (str): --
            cosim_method (str): cosimulation algorithm to use
            iterative (str): whether cosimulation algorithm is iterative or not
            kwargs (any): additional arguments, not used
        """
        self.fmus = [ConfigFmu(**fmu_dict) for fmu_dict in fmus]
        if connections is None:
            connections = []
        self.connections = [
            ConfigConnection(**connection_dict) for connection_dict in connections
        ]
        if data_storages is None:
            data_storages = []
        self.data_storages = [
            ConfigDataStorage(**storage_dict) for storage_dict in data_storages
        ]
        self.edge_sep = edge_sep
        self.cosim_method = cosim_method
        self.iterative = iterative
        self.root = root

        # Add warning for not used properties
        for arg in kwargs:
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        """
        Construct and return object as a dictionary
        Returns:
            object as a dictionary.
        """
        connections = []
        for connection in self.connections:
            for target in connection.target:
                connections.append(
                    {"source": connection.source.asdict(), "target": target.asdict()}
                )
        return {
            "root": self.root,
            "edge_sep": self.edge_sep,
            "cosim_method": self.cosim_method,
            "iterative": self.iterative,
            "fmus": [fmu.asdict() for fmu in self.fmus],
            "connections": connections,
            "data_storages": [storage.asdict() for storage in self.data_storages],
        }
