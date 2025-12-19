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
Services methods for Flask server
"""
import os
import json
from cofmupy.utils import fmu_utils


def retrieve_project_from_params(project_path: str, project_id: str):
    """
    Retrieve project from name and id. find project sub-directory of the root path,
        and check consistency with project id

    Args:
        project_path (str): path of the project, correspond to sub-directory
            inside root directory
        project_id (str): project id. Used to check consistency

    Returns:
        dict: config dictionary amended with additional data.
    """
    if not os.path.exists(project_path):
        raise Exception("Project doesn't exist")

    with open(
        os.path.join(project_path, "metadata.json"),
        "r",
        encoding="utf-8",
    ) as file:
        project = json.load(file)
        # Check project id
        if project["id"] != project_id:
            raise Exception("Bad project id")

    return project


def transform_config_for_frontend(config: dict, project_path: str):
    """
    Complete config fmu sections with fmu details (input and output ports)

    Args:
        config (dict): dictionary with configuration sections.
        project_path (str): path of the project

    Returns:
        dict: config dictionary amended with additional data.
    """
    for fmu in config["fmus"]:
        table_result = fmu_utils.retrieve_fmu_info(
            os.path.join(project_path, fmu["path"])
        )
        input_ports = []
        output_ports = []
        if table_result is not None:
            for line in table_result:
                excluded = False
                if not excluded:
                    if line["category"] == "Input":
                        input_ports.append(line)
                    if line["category"] == "Output":
                        output_ports.append(line)
        fmu["inputPorts"] = input_ports
        fmu["outputPorts"] = output_ports
    return config


def transform_config_from_frontend(config: dict):
    """
    Refactor configuration dict

    Args:
        config (dict): dictionary with configuration sections.

    Returns:
        dict: refactored config dictionary, ready to save in json file.
    """
    # Refactor connections to expected format
    factorized_connections = []
    for connection in config["connections"]:
        # Look for existing item with same source
        found_source = False
        for fact_connection in factorized_connections:
            fact_source = fact_connection["source"]
            if (
                fact_source["id"] == connection["source"]["id"]
                and fact_source["variable"] == connection["source"]["variable"]
            ):
                fact_connection["target"].extend([connection["target"]])
                found_source = True
        if not found_source:
            factorized_connections.append(
                {"source": connection["source"], "target": [connection["target"]]}
            )
    config["connections"] = factorized_connections

    # Refactor fmu to remove inputPorts and outputPorts
    for fmu in config["fmus"]:
        if "inputPorts" in fmu:
            del fmu["inputPorts"]
        if "outputPorts" in fmu:
            del fmu["outputPorts"]
        if "info" in fmu:
            del fmu["info"]

    # Refactor data_storages before save : remove config.items and config.labels
    for storage in config["data_storages"]:
        del storage["config"]["items"]
        del storage["config"]["labels"]

    return config
