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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
This module is designed to parse, validate, and structure a JSON
configuration file for the co-simulation framework. It ensures that all
necessary configurations for GraphEngine, Master DataStreamHandlers, and
DataStorages are correctly formatted and ready for execution.
Additionally, it performs sanity checks to detect missing keys,
redundant endpoints, and orphaned connections.
"""
import json
import logging
import os
from typing import Dict
from typing import List
from typing import Union

from .config_interface import ConfigConnectionFmu
from .config_interface import ConfigConnectionStorage
from .config_interface import ConfigConnectionLocalStream
from .config_interface import ConfigConnectionCsvStream
from .config_interface import ConfigObject
from .config_interface import FMU_TYPE

logger = logging.getLogger(__name__)


class ConfigParser:
    """
    Parses and validates JSON configuration files.

    This class handles loading, validation, and transformation of configuration data
    for various components such as the Graph Engine, Master Solver, Data Storages,
    and Stream Handlers.

    Attributes:
        file_path (Union[str, Dict]): Path to the configuration file. Can also be
            a dictionary if the user prefers to provide the configuration directly
            without using a JSON file.
        _config_object (ConfigObject): The parsed configuration object (type
            ConfigObject)
        graph_config (Dict): Configuration for the graph engine.
        master_config (Dict): Configuration for the master solver.
        data_storages (Dict): Storage settings for external data.
        stream_handlers (Dict): Handlers for external data streams.
        error_in_config (bool): Indicates whether errors exist in the configuration.
    """

    def __init__(self, file_path: Union[str, Dict]) -> None:
        # Arguments
        self.file_path = file_path

        self._config_object: ConfigObject
        self.graph_config: Dict = {}
        self.master_config: Dict = {}
        self.data_storages: Dict = {}
        self.stream_handlers: Dict = {}
        self.error_in_config: bool = False

        # ------------ 1. Load config: self._config_object ------------------
        self._config_object = self._load_config(file_check=True)

        # ------------ 2. Apply defaults and perform validation ------------
        self._validate_configuration()

        # ------------ 3. Build configurations ---------------------------
        self._build_storage_config()
        self._build_master_config()
        self._build_handlers_config()
        self._build_graph_config()

    @property
    def config_dict(self):
        """
        Construct and return dict from protected _config_object

        Returns:
            config (dict): config formatted as a dict
        """
        return self._config_object.asdict()

    def _load_config(self, file_check: bool) -> ConfigObject:
        """Load JSON configuration from a file or dictionary."""
        if isinstance(self.file_path, dict):
            # If input is a dictionary, use directly.
            config_object = ConfigObject(**self.file_path)
            return config_object

        if isinstance(self.file_path, str) and self.file_path.endswith(".json"):
            if file_check and not os.path.exists(self.file_path):
                raise FileNotFoundError(
                    f"Configuration file not found: {self.file_path}"
                )

            with open(self.file_path, "r", encoding="utf-8") as file:

                my_dict = json.load(file)
                config_object = ConfigObject(**my_dict)
                return config_object

        raise TypeError(f"Invalid configuration format: {type(self.file_path)}")

    def _build_storage_config(self):
        for storage in self._config_object.data_storages:
            storage_dict = storage.__dict__
            storage_dict["config"]["labels"] = []
            storage_dict["config"]["items"] = []
            self.data_storages[storage.name] = storage_dict

    def _build_graph_config(self) -> None:
        """Build configuration dict for the graph engine.

        The graph engine requires three information: the FMUs,
        the connections and the edge separator.

        Returns:
            None. Builds self.graph_config.
        """
        self.graph_config = {}
        self.graph_config["fmus"] = [fmu.asdict() for fmu in self._config_object.fmus]
        self.graph_config["symbolic_nodes"] = self._add_symbolic_nodes()
        self.graph_config["connections"] = []
        self.graph_config["edge_sep"] = self._config_object.edge_sep

        for connection in self._config_object.connections:
            for target_unit in connection.target:
                if connection.source.type == FMU_TYPE and target_unit.type == FMU_TYPE:
                    graph_conn = {
                        "source": {
                            "id": connection.source.id,
                            "variable": connection.source.variable,
                            "unit": connection.source.unit,
                        },
                        "target": {
                            "id": target_unit.id,
                            "variable": target_unit.variable,
                            "unit": target_unit.unit,
                        },
                    }
                    self.graph_config["connections"].append(graph_conn)

    def _build_master_config(self) -> None:
        """Build configuration dictionary for the Master.

        The Master requires:
        - the list of FMUs (external data sources like csv)
        - the connections (as a dict where keys are tuples (fmu_id, variable_name))
        - the sequence order (computed by the graph engine, so set to None here)
        - the loop method for solving algebraic loops in the co-simulation.

        Returns:
            None. Builds self.master_config.
        """

        fmus = []
        for fmu in self._config_object.fmus:
            fmu = fmu.asdict()
            fmu["path"] = self._find_corrected_relative_path(fmu["path"])
            fmus.append(fmu)
        self.master_config["fmus"] = fmus
        self.master_config["connections"] = {}
        self.master_config["sequence_order"] = None
        self.master_config["cosim_method"] = self._config_object.cosim_method
        self.master_config["iterative"] = self._config_object.iterative

        for connection in self._config_object.connections:
            source = connection.source
            for target in connection.target:

                if source.type == target.type == FMU_TYPE:
                    # Initialize list of connections from source if not yet present
                    if (source.id, source.variable) not in self.master_config[
                        "connections"
                    ]:
                        self.master_config["connections"][
                            (source.id, source.variable)
                        ] = []

                    # Append target connection to the source
                    self.master_config["connections"][
                        (source.id, source.variable)
                    ].append((target.id, target.variable))

    def _build_handlers_config(self) -> None:
        """
        Build configurations for stream handlers and data storages.

        This method iterates over connections in the configuration dictionary,
        identifies external data sources and targets, and creates corresponding
        handler configurations. Handlers/storages are attributed according to:
        * If data type is external and is a 'source' -> stream handler
        * If data type is external and is a 'target' -> data storage

        Returns:
            None. Builds self.data_storages and self.stream_handlers.
        """
        self.stream_handlers = {}
        for connection in self._config_object.connections:
            source = connection.source
            for target in connection.target:

                # source is external data
                if isinstance(
                    source, (ConfigConnectionLocalStream, ConfigConnectionCsvStream)
                ):
                    if isinstance(source, ConfigConnectionLocalStream):
                        handler_val = {
                            "type": source.type,
                            "config": {
                                "values": source.values,
                                "interpolation": source.interpolation,
                            },
                        }
                    else:
                        handler_val = {
                            "type": source.type,
                            "config": {
                                "path": source.path,
                                "variable": source.variable,
                                "interpolation": source.interpolation,
                            },
                        }
                    # If target is FMU => it's a stream handler
                    if isinstance(target, ConfigConnectionFmu):
                        handler_key = (target.id, target.variable)
                        if handler_key not in self.stream_handlers:
                            self.stream_handlers[handler_key] = handler_val
                    # Si ce n'est pas un fmu, c'est un input à stocker dans les storages
                    elif isinstance(target, ConfigConnectionStorage):
                        self.fill_data_storage(
                            connection.target, target.id, target.alias
                        )

                # target is external data
                elif isinstance(target, ConfigConnectionStorage):
                    # Add item to data_storage items
                    self.data_storages[target.id]["config"]["labels"].append(
                        target.alias
                    )
                    self.data_storages[target.id]["config"]["items"].append(
                        (source.id, source.variable)
                    )

    def fill_data_storage(self, targets: list, storage_id: str, storage_title: str):
        """
        Fill data storage with labels and items
        """
        for target2 in targets:
            if isinstance(target2, ConfigConnectionFmu):
                self.data_storages[storage_id]["config"]["labels"].append(storage_title)
                self.data_storages[storage_id]["config"]["items"].append(
                    (target2.id, target2.variable)
                )

    def _add_symbolic_nodes(self) -> List:
        """
        Search for external data connections in:
        * self._config_object.connections.source
        * self._config_object.connections.target
        i.e. if their type is not "fmu".
        If present, add a symbolic node to self._config_object.fmus.
        Also required fields for graph configuration: 'id', 'variable'

        Such a node is a dictionary with the contents:
        * 'id': unique id:
            <direction ('source' or 'target')>_<data type>_<variable or na>
        * 'id_as_list': unique id as a list:
            [<direction ('source' or 'target')>, <data type>, <variable or na>]
        * 'loc': index in self._config_object.connections list
            and direction ('source' or 'target').

        Example of symbolic node:
        ```python
        symbolic_node = {
            'id': 'source_literal_na',
            'id_as_list': ['source', 'literal', 'na'],
            'loc': [0, 'source']
        }
        ```
        """
        symbolic_nodes = []
        # Explore all sources and targets in the connections
        for conn_index, connection in enumerate(self._config_object.connections):
            if connection.source.type != FMU_TYPE:
                if connection.source.variable == "":
                    connection.source.variable = "na"
                id_ = f"source_{connection.source.type}_{connection.source.variable}"
                id_as_list_ = [
                    "source",
                    connection.source.type,
                    connection.source.variable,
                ]
                symbolic_node = {
                    "id": id_,
                    "id_as_list": id_as_list_,
                    "loc": [conn_index, "source"],
                }
                symbolic_nodes.append(symbolic_node)
                connection.source.id = id_
            """
            for target in connection.target:
                if target.type != FMU_TYPE:
                    if target.variable == "":
                        target.variable = "na"
                    id_ = f"target_{target.type}_{target.variable}"
                    id_as_list_ = ["target", target.type, target.variable]
                    symbolic_node = {
                        "id": id_,
                        "id_as_list": id_as_list_,
                        "loc": [conn_index, "target"],
                    }
                    symbolic_nodes.append(symbolic_node)
                    connection.source.id = id_
            """

        return symbolic_nodes

    def _validate_configuration(self) -> None:
        """Perform sanity checks on the configuration.
        missing_keys
        external_loops
        orphan_connections
        outlier_connections
        redundant_endpoints
        """
        # TODO

    def _find_corrected_relative_path(self, path: str) -> str:
        """
        Finds the correct relative path for `path`, ensuring it is located within
        or below the directory of `self.file_path`.

        - If `self.file_path` is a dictionary (config passed as dict),
          the base directory is set to the current working directory (`os.getcwd()`).
        - Otherwise, the base directory is derived from `self.file_path`.

        If `path` is not found within the expected directory structure, a warning is
        logged,
        and the function returns `path` unchanged.

        Args:
            path (str): The relative path of the file to locate.

        Returns:
            str: The corrected relative path to `path` from `os.getcwd()`,
                or `path` if not found.
        """
        # If no correction needed, return provided path
        if os.path.exists(path):
            logger.info(f"Success: found {path}")
            return path

        if ".py" in path and "::" in path:
            module_name = path.split("::")[0]
            class_name = path.split("::")[1]
            if os.path.exists(module_name):
                logger.info(
                    f"Success: {path} resolved to module: {module_name}, class: {class_name}"
                )
                return path

        # Determine the base directory
        if isinstance(self.file_path, dict):
            base_dir = os.getcwd()
        else:
            base_dir = os.path.dirname(self.file_path)

        # Search for file inside base_dir, return corrected relative path
        for root, _, files in os.walk(base_dir):
            if os.path.basename(path) in files:
                abs_path_corrected = os.path.join(root, os.path.basename(path))
                rel_path_corrected = os.path.relpath(abs_path_corrected, os.getcwd())
                logger.info(f"Info: {path} replaced by: {rel_path_corrected}")
                return rel_path_corrected

        # File not found: log warning and return the original path
        logger.error(f"File not found: {path} (searched recursively in {base_dir})")
        return path

    def _update_paths_in_dict(
        self,
    ) -> None:
        """
        Update the relative paths in the configuration dictionary to ensure they are
        located within or below the directory of `self.file_path`. This method is used
        to correct paths for FMUs.
        """

        for fmu_dict in self._config_object.fmus:
            fmu_dict.path = self._find_corrected_relative_path(fmu_dict.path)
