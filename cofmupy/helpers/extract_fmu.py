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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
This module provides a command-line utility to extract and display information from an
FMU file.
"""
import argparse
import os
import shutil

from fmpy import extract
from fmpy import read_model_description
from rich.console import Console
from rich.table import Table

import csv


def extract_fmu_info(fmu_path, output_file):
    """
    Extracts information from an FMU file and displays it in a structured format.

    Args:
        fmu_path (str): Path to the FMU file.
        output_file (str): Path to the optional output file (csv file)

    """
    console = Console()

    # Ensure FMU exists
    if not os.path.isfile(fmu_path):
        console.print(f"[red]❌ Error: FMU file '{fmu_path}' not found.[/red]")
        return

    has_output_file = False
    spam_writer = None
    # check output file requested. If yes => extract information to file
    if output_file is not None:
        has_output_file = True
        print(f"Create file {output_file}")
        csvfile = open(output_file, 'w', newline='')
        spam_writer = csv.writer(
            csvfile, delimiter=',',
            quotechar='|', quoting=csv.QUOTE_MINIMAL
        )
        spam_writer.writerow(['Category', 'name', 'type', 'type', 'unit', 'start_value'])

    # Extract FMU content
    unpacked_fmu_dir = extract(fmu_path)
    model_desc = read_model_description(fmu_path)

    # Prepare table
    table = Table(
        title=f"📜 FMU Information: {os.path.basename(fmu_path)}", show_lines=True
    )
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Variable", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Unit", style="green")
    table.add_column("Start Value", style="white")

    # FMU version
    fmu_version = model_desc.fmiVersion if model_desc.fmiVersion else "N/A"
    console.print(f"📦 [bold]FMU Version:[/bold] {fmu_version}", style="blue")

    # Integration step size (if available)
    step_size = (
        model_desc.defaultExperiment.stepSize if model_desc.defaultExperiment else "N/A"
    )
    console.print(
        f"🕒 [bold]Default Integration Step Size:[/bold] {step_size}\n", style="blue"
    )

    # Iterate through variables
    for variable in model_desc.modelVariables:
        category = (
            "Parameter"
            if variable.causality == "parameter"
            else variable.causality.capitalize()
        )
        name = variable.name
        var_type = variable.variability.capitalize()
        var_unit = variable.unit
        start_value = variable.start if variable.start is not None else "-"

        # Append table row for console display
        table.add_row(category, name, var_type, var_unit, str(start_value))

        # Append line into csv file (if output file)
        if has_output_file:
            spam_writer.writerow(
                [
                    category,
                    variable.name,
                    variable.variability,
                    variable.type,
                    variable.unit,
                    str(start_value)
                ]
            )

    # Display table
    console.print(table)

    # Cleanup extracted FMU folder
    shutil.rmtree(unpacked_fmu_dir, ignore_errors=True)

    print(output_file)


def main():
    """
    Main function to parse command-line arguments and call the extraction function.

    command line example to extract info from my_fmu.fmu to extract_infos.csv file :
        >> python extract_fmu.py my_fmu.fmu" --output_file "./extract_infos.csv"
    """
    parser = argparse.ArgumentParser(
        description="Extracts and displays FMU information in a structured format."
    )
    parser.add_argument("fmu_file", help="Path to the FMU file")
    parser.add_argument("--output_file", help="Path to the output file", required=False)
    args = parser.parse_args()

    extract_fmu_info(args.fmu_file, args.output_file)


if __name__ == "__main__":
    main()
