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
This module is designed to parse, validate, and structure a JSON
configuration file for the co-simulation framework. It ensures that all
necessary configurations for GraphEngine, Master DataStreamHandlers, and
DataStorages are correctly formatted and ready for execution.
Additionally, it performs sanity checks to detect missing keys,
redundant endpoints, and orphaned connections.
"""

import os
import json
import logging
from typing import Union, Dict, List
from copy import deepcopy

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
        edge_sep (str): Edge separator for connections. Defaults to " -> ".
        loop_solver (str): Method used to solve algebrauc loops. Defaults to "jacobi".
        config_dict (Dict): The parsed configuration dictionary.
        graph_config (Dict): Configuration for the graph engine.
        master_config (Dict): Configuration for the master solver.
        data_storages (Dict): Storage settings for external data.
        stream_handlers (Dict): Handlers for external data streams.
        error_in_config (bool): Indicates whether errors exist in the configuration.
    """

    def __init__(
        self,
        file_path: Union[str, Dict],
        edge_sep: str = " -> ",
        loop_solver: str = "jacobi",
    ) -> None:
        # Arguments
        self.file_path = file_path
        self.loop_solver = loop_solver
        self.edge_sep = edge_sep

        self.config_dict: Dict = {}
        self.graph_config: Dict = {}
        self.master_config: Dict = {}
        self.data_storages: Dict = {}
        self.stream_handlers: Dict = {}
        self.error_in_config: bool = False

        # ------------ 1. Load config: self.config_dict ------------------
        self.config_dict = self._load_config(file_check=True)

        # ------------ 2. Apply defaults and perform validation ------------
        self._apply_defaults(edge_sep, loop_solver)
        self._validate_configuration()

        # ------------ 3. Prepend 'root' dir to present paths ------------
        self._update_paths_in_dict()

        # ------------ 4. Build configurations ---------------------------
        self._build_master_config()
        self._build_handlers_config()
        self._build_graph_config()

    def _load_config(self, file_check: bool) -> Dict:
        """Load JSON configuration from a file or dictionary."""
        if isinstance(self.file_path, dict):
            return self.file_path  # If input is a dictionary, use directly.

        if isinstance(self.file_path, str) and self.file_path.endswith(".json"):
            if file_check and not os.path.exists(self.file_path):
                raise FileNotFoundError(
                    f"Configuration file not found: {self.file_path}"
                )

            with open(self.file_path, "r", encoding="utf-8") as file:
                return json.load(file)

        raise TypeError(f"Invalid configuration format: {type(self.file_path)}")

    def _apply_defaults(self, edge_sep: str, loop_solver: str) -> None:
        """Apply default values to missing configuration fields."""
        self.config_dict.setdefault("root", "")
        self.config_dict.setdefault("loop_solver", loop_solver)
        self.config_dict.setdefault("edge_sep", edge_sep)

        # Add connections if not present
        self.config_dict["connections"] = self.config_dict.get("connections", [])

        for connection in self.config_dict["connections"]:
            for _, fields in connection.items():
                fields.setdefault("type", "fmu")
                fields.setdefault("unit", "")

        for fmu in self.config_dict.get("fmus", []):
            fmu.setdefault("initialization", {})

    def _build_graph_config(self) -> None:
        """Build configuration dict for the graph engine.

        The graph engine requires three information: the FMUs,
        the connections and the edge separator.

        Returns:
            None. Builds self.graph_config.
        """
        self.graph_config = {}
        self.graph_config["fmus"] = self.config_dict["fmus"]
        self.graph_config["symbolic_nodes"] = self._add_symbolic_nodes()
        self.graph_config["connections"] = []
        self.graph_config["edge_sep"] = self.config_dict["edge_sep"]

        for connection in self.config_dict["connections"]:
            # Ignore symbolic nodes if method is not used (for future use)
            if "id" in connection["source"] and "id" in connection["target"]:
                graph_conn = {
                    "source": {
                        "id": connection["source"]["id"],
                        "variable": connection["source"]["variable"],
                        "unit": connection["source"]["unit"],
                    },
                    "target": {
                        "id": connection["target"]["id"],
                        "variable": connection["target"]["variable"],
                        "unit": connection["target"]["unit"],
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

        self.master_config["fmus"] = self.config_dict["fmus"]
        self.master_config["connections"] = {}
        self.master_config["sequence_order"] = None
        self.master_config["loop_solver"] = self.config_dict["loop_solver"]

        for connection in self.config_dict["connections"]:
            source = connection["source"]
            target = connection["target"]

            if source["type"] == target["type"] == "fmu":
                # Initialize list of connections from source if not yet present
                if (source["id"], source["variable"]) not in self.master_config[
                    "connections"
                ]:
                    self.master_config["connections"][
                        (source["id"], source["variable"])
                    ] = []

                # Append target connection to the source
                self.master_config["connections"][
                    (source["id"], source["variable"])
                ].append((target["id"], target["variable"]))

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
        self.data_storages = {}
        for connection in self.config_dict["connections"]:
            source = connection["source"]
            target = connection["target"]

            # source is external data
            if source["type"] != "fmu":
                type_ = source["type"]
                config = deepcopy(source)
                del config["type"]
                del config["unit"]
                _ = config.pop("id", None)

                handler_key = (target["id"], target["variable"])
                handler_val = {
                    "type": type_,
                    "config": config,
                }
                self.stream_handlers[handler_key] = handler_val

            # target is external data
            elif target["type"] != "fmu":
                type_ = target["type"]
                config = deepcopy(target)
                del config["type"]
                del config["unit"]
                _ = config.pop("id", None)

                handler_key = (source["id"], source["variable"])
                handler_val = {
                    "type": type_,
                    "config": config,
                }
                self.data_storages[handler_key] = handler_val

    def _add_symbolic_nodes(self) -> List:
        """
        Search for external data connections in:
        * self.config_dict['connections']['sources']
        * self.config_dict['connections']['targets']
        i.e. if their type is not "fmu".
        If present, add a symbolic node to self.config_dict['fmus'].
        Also required fields for graph configuration: 'id', 'variable'

        Such a node is a dictionary with the contents:
        * 'id': unique id:
            <direction ('source' or 'target')>_<data type>_<variable or na>
        * 'id_as_list': unique id as a list:
            [<direction ('source' or 'target')>, <data type>, <variable or na>]
        * 'loc': index in self.config_dict['connections'] list
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
        for conn_index, connection in enumerate(self.config_dict["connections"]):
            for direction, value in connection.items():
                type_ = value["type"]
                if type_ != "fmu":
                    var = value.get("variable", "na")
                    id_ = f"{direction}_{type_}_{var}"
                    symbolic_node = {
                        "id": id_,
                        "id_as_list": [direction, type_, var],
                        "loc": [conn_index, direction],
                    }
                    # append symbolic_node to "fmus"
                    symbolic_nodes.append(symbolic_node)
                    # Add id and variable to connections
                    self.config_dict["connections"][conn_index][direction]["id"] = id_
                    self.config_dict["connections"][conn_index][direction][
                        "variable"
                    ] = var

        return symbolic_nodes

    def _validate_configuration(self) -> None:
        """Perform sanity checks on the configuration.
        missing_keys
        external_loops
        orphan_connections
        outlier_connections
        redundant_endpoints
        """
        # TODO: use jsonschema to validate the configuration
        required_keys = ["fmus", "connections"]
        missing_keys = [key for key in required_keys if key not in self.config_dict]

        if missing_keys:
            self.error_in_config = True
            logger.error(f"Missing required configuration keys: {missing_keys}")
            raise ValueError(f"Missing required keys: {missing_keys}")

    def _find_corrected_relative_path(self, path: str) -> str:
        """
        Finds the correct relative path for `path`, ensuring it is located within
        or below the directory of `self.file_path`.

        - If `self.file_path` is a dictionary (config passed as dict),
          the base directory is set to the current working directory (`os.getcwd()`).
        - Otherwise, the base directory is derived from `self.file_path`.

        If `path` is not found within the expected directory structure, a warning is logged,
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
        target_key: str = "path",
    ) -> None:
        """
        Update the relative paths in the configuration dictionary to ensure they are
        located within or below the directory of `self.file_path`. This method is used
        to correct paths for FMUs.

        Args:
            target_key (str): The key in the configuration dictionary to update.
                Defaults to "path".
        """

        for fmu_dict in self.config_dict["fmus"]:
            if target_key in fmu_dict.keys():
                fmu_dict[target_key] = self._find_corrected_relative_path(
                    fmu_dict[target_key]
                )
