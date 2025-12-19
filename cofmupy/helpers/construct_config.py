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
This module provides a command-line utility to construct config file from connection
list and initialisation list
"""
import argparse
import os
from fmpy import read_model_description
from rich.console import Console

import csv
import pprint
import json


def check_fmu_variable(fmu_file, variable_name, from_to):
    """
    Check variables exist inside the fmu, with the good type for the connection.
        Errors log inside console and return error status.

    Args:
        fmu_file: fmu file where variable is expected.
        variable_name: The name of the variable to find.
        from_to : 'from' if variable is expected as output, 'to' for input

    Returns:
        Result of the check : True if variable found and type is ok. otherwise False
    """
    model_desc = read_model_description(fmu_file)
    for variable in model_desc.modelVariables:
        if variable.name == variable_name:
            if from_to == "from" and variable.causality == "Input":
                Console().print(
                    f"❌ Error: variable '{variable_name}' on {fmu_file} "
                    f"has {variable.causality} type. It can't be used as source."
                )
                return False
            if from_to == "to" and variable.causality == "Output":
                Console().print(
                    f"❌ Error: variable '{variable_name}' on {fmu_file} "
                    f"has {variable.causality} type. It can't be used as target."
                )
                return False
            return True

    Console().print(f"❌ Error: variable '{variable_name}' not found in {fmu_file}.")
    return False


def check_fmus(csvfile_connections, csvfile_initializations=None):
    """
    Check input files, connections list and initialisation list :
        - Check expected fmus exist
        - Check variables exist inside fmu with the correct type for the connections
        log all found error in console and raise an Exception at the end

    Args:
        csvfile_connections: connection list file (csv). Expected columns are :
            - 'from_path' : path of the source fmu
            - 'from_id' : id of the source fmu
            - 'from_name' : expected name of the source fmu
            - 'from_var_name' : name of the source variable
            - 'to_path' : path of the target fmu
            - 'to_id' : id of the target fmu
            - 'to_name' : expected name of the target fmu
            - 'to_var_name' : name of the target variable
        csvfile_initializations: initialisation list file (csv). Default is None
        Expected columns are :
            - 'Fmu_id' : id of the concerned fmu
            - 'Variable' : name of the variable to initialize
            - 'Value' : value of the variable

    Returns:
        Result of the check : true if all is ok.
    """
    fmu_file_dict = {}
    error = False

    csvfile_connections.seek(0)
    connection_itr = csv.DictReader(csvfile_connections)
    for row in connection_itr:
        # Check fmu files exists
        from_fmu_file = row["from_path"] + "/" + row["from_name"]
        if not os.path.isfile(from_fmu_file):
            raise Exception(f"Error: FMU file '{from_fmu_file}' not found.")

        to_fmu_file = row["to_path"] + "/" + row["to_name"]
        if not os.path.isfile(to_fmu_file):
            raise Exception(f"Error: FMU file '{to_fmu_file}' not found.")

        if row["from_id"] not in fmu_file_dict:
            fmu_file_dict[row["from_id"]] = from_fmu_file
        if row["to_id"] not in fmu_file_dict:
            fmu_file_dict[row["to_id"]] = to_fmu_file

        # Check from :
        #   - Variable name exists
        #   - Type is output
        if not check_fmu_variable(from_fmu_file, row["from_var_name"], "from"):
            error = True

        # Check to :
        #   - Variable name exists
        #   - Type is input
        if not check_fmu_variable(to_fmu_file, row["to_var_name"], "to"):
            error = True

    # Check connection list
    if csvfile_initializations is not None:
        csvfile_initializations.seek(0)
        initialisation_itr = csv.DictReader(csvfile_initializations)
        for row in initialisation_itr:
            # check fmu id exists into connections list
            if row["Fmu_id"] not in fmu_file_dict:
                Console().print(
                    f"❌ Error: FMU id {row['Fmu_id']} not found in connections."
                )
                error = True
                continue

            # Check Variable name exists
            if not check_fmu_variable(
                fmu_file_dict[row["Fmu_id"]], row["Variable"], "init"
            ):
                error = True
    if error:
        raise Exception("Problems occurs on check FMUs, see details above")
    return True


def find_initialisations_for_fmu(csvfile_initializations, fmu_id):
    """
    Find all initialisations concerned by the given fmu id.

    Args:
        csvfile_initializations: initialisation list file (csv).
        Expected columns are :
            - 'Fmu_id' : id of the concerned fmu
            - 'Variable' : name of the variable to initialize
            - 'Value' : value of the variable
        fmu_id : id of the fmu for which we are looking for the initialisations

    Returns:
        Dictionary of all initialisations for the given fmu.
    """
    if csvfile_initializations is None:
        return {}

    initialisation_dict = {}
    csvfile_initializations.seek(0)
    initialisation_itr = csv.DictReader(csvfile_initializations)
    for row in initialisation_itr:
        if row["Fmu_id"] == fmu_id:
            initialisation_dict[row["Variable"]] = row["Value"]

    return initialisation_dict


def construct_fmu_list(csvfile_connections, csvfile_initializations=None):
    """
    Construct fmu list (config format) from connection list (tabular format) and
        initialisation list : Parse information from connections iterator to construct
        "fmus" section. If expected, append with initialisations on each fmu.

    Args:
        csvfile_connections: connection list file (csv). Expected columns are :
            - 'from_path' : path of the source fmu
            - 'from_id' : id of the source fmu
            - 'from_name' : expected name of the source fmu
            - 'from_var_name' : name of the source variable
            - 'to_path' : path of the target fmu
            - 'to_id' : id of the target fmu
            - 'to_name' : expected name of the target fmu
            - 'to_var_name' : name of the target variable
        csvfile_initializations: initialisation list file (csv). Default is None
        Expected columns are :
            - 'Fmu_id' : id of the concerned fmu
            - 'Variable' : name of the variable to initialize
            - 'Value' : value of the variable

    Returns:
        Object list of FMUs (config file format).
    """
    fmus = []
    csvfile_connections.seek(0)
    connection_itr = csv.DictReader(csvfile_connections)
    for row in connection_itr:

        fmu_from = {
            "id": row["from_id"],
            "name": row["from_id"],
            "path": row["from_path"] + "/" + row["from_name"],
            "initialization": find_initialisations_for_fmu(
                csvfile_initializations, row["from_id"]
            ),
        }
        fmu_to = {
            "id": row["to_id"],
            "name": row["to_id"],
            "path": row["to_path"] + "/" + row["to_name"],
            "initialization": find_initialisations_for_fmu(
                csvfile_initializations, row["to_id"]
            ),
        }
        if fmu_from not in fmus:
            fmus.append(fmu_from)
        if fmu_to not in fmus:
            fmus.append(fmu_to)

    return fmus


def construct_exported_outputs_list(csvfile_connections):
    """
    Construct exported output list from connection list : all sources

    Args:
        csvfile_connections: connection list file (csv). Expected columns are :
            - 'from_path' : path of the source fmu
            - 'from_id' : id of the source fmu
            - 'from_name' : expected name of the source fmu
            - 'from_var_name' : name of the source variable
            - 'to_path' : path of the target fmu
            - 'to_id' : id of the target fmu
            - 'to_name' : expected name of the target fmu
            - 'to_var_name' : name of the target variable

    Returns:
        Dictionary of all exported signals.
    """
    exported_outputs = []
    csvfile_connections.seek(0)
    connection_itr = csv.DictReader(csvfile_connections)
    for row in connection_itr:
        exported_outputs.append(row["from_id"] + "." + row["from_var_name"])

    exported_outputs.sort()
    return exported_outputs


def construct_connection_list(csvfile_connections):
    """
    Construct connection list (config format) from connection list (tabular format) :
        Parse information from connections iterator to construct "connections"
            section ready to integrate into config file

    Args:
        csvfile_connections: connection list file (csv). Expected columns are :
            - 'from_path' : path of the source fmu
            - 'from_id' : id of the source fmu
            - 'from_name' : expected name of the source fmu
            - 'from_var_name' : name of the source variable
            - 'to_path' : path of the target fmu
            - 'to_id' : id of the target fmu
            - 'to_name' : expected name of the target fmu
            - 'to_var_name' : name of the target variable

    Returns:
        Object list of FMU connections (config file format).
    """

    connections = []
    csvfile_connections.seek(0)
    connection_itr = csv.DictReader(csvfile_connections)
    for row in connection_itr:

        connections.append(
            {
                "source": {
                    "type": "fmu",
                    "id": row["from_id"],
                    "variable": row["from_var_name"],
                    "unit": "",
                },
                "target": {
                    "type": "fmu",
                    "id": row["to_id"],
                    "variable": row["to_var_name"],
                    "unit": "",
                },
            }
        )
    return connections


def construct_config(connections_path, initializations_path):
    """
    Construct global config file for CoFmuPy :
        Parse information from connections file to construct "fmus" and "connections"
            sections
        parse initializations file to append to "fmus" section

    Args:
        connections_path (str): Path to the connections file.
        initializations_path (str): Path to the optional initializations file
    """
    has_init_file = False

    # Ensure files exists
    if not os.path.isfile(connections_path):
        Console().print(f"❌ Error: Connection list '{connections_path}' not found.")
        return

    # check initializations file provided, and exists
    if initializations_path is not None:
        has_init_file = True
        if not os.path.isfile(initializations_path):
            Console().print(
                f"❌ Error: Initialization list '{initializations_path}' not found."
            )
            return

    # Open and read connections_path file
    with open(connections_path, newline="", encoding="utf-8") as csvfile_connections:

        # Open and read initializations_path file (if any)
        if has_init_file:
            with open(
                initializations_path, newline="", encoding="utf-8"
            ) as csvfile_initializations:
                # Check connection_list contains correct paths to fmu
                check_fmus(csvfile_connections, csvfile_initializations)

                fmus = construct_fmu_list(csvfile_connections, csvfile_initializations)
        else:
            # Check connection_list contains correct paths to fmu
            check_fmus(csvfile_connections)

            fmus = construct_fmu_list(csvfile_connections)
        connections = construct_connection_list(csvfile_connections)
        exported_outputs = construct_exported_outputs_list(csvfile_connections)

        # build final config file
        config = {
            "fmus": fmus,
            "connections": connections,
            "exported_outputs": exported_outputs,
            "edge_sep": "->",
            "cosim_method": "jacobi",
        }

        # Pretty print final config file into the console (json format)
        pprint.pp(config, compact=False)
        Console().print(f"Found {len(fmus)} fmus")
        if connections is not None:
            Console().print(f"Found {len(connections)} connections")

        with open("config.json", "w", encoding="utf-8") as fp:
            json.dump(config, fp, indent=4)


def main():
    """
    Main function to parse command-line arguments and call the extraction function.
    """
    parser = argparse.ArgumentParser(
        description="Extracts and displays FMU information in a structured format."
    )
    parser.add_argument(
        "connections_file", help="Path to the file that contains fmus connections"
    )
    parser.add_argument(
        "--initializations_file",
        help="Path to the file that contains fmus initializations",
        required=False,
    )
    args = parser.parse_args()

    construct_config(args.connections_file, args.initializations_file)


if __name__ == "__main__":
    main()
