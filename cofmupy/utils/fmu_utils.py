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
This module provides utilities on FMU file.
"""
import os
import fmpy
from rich.console import Console


def retrieve_fmu_info(fmu_path):
    """
    Retrieve information from an FMU file and return variable list.

    Args:
        fmu_path (str): Path to the FMU file.
    """

    # Ensure FMU exists
    if not os.path.isfile(fmu_path):
        Console().print(f"[red]❌ Error: FMU file '{fmu_path}' not found.[/red]")
        return []

    # Extract FMU content
    model_desc = fmpy.read_model_description(fmu_path)

    # Iterate through variables
    variables = []
    for model_variable in model_desc.modelVariables:
        category = (
            "Parameter"
            if model_variable.causality == "parameter"
            else model_variable.causality.capitalize()
        )

        if category != "Local":
            variable = {
                "name": model_variable.name,
                "type": model_variable.variability.capitalize(),
                "start": (
                    model_variable.start if model_variable.start is not None else "-"
                ),
                "category": category,
            }
            variables.append(variable)

    return variables


def get_model_description(fmu_path):
    """
    Retrieve information from an FMU file and return variable list.

    Args:
        fmu_path (str): Path to the FMU file.
    """

    # Ensure FMU exists
    if not os.path.isfile(fmu_path):
        Console().print(f"[red]❌ Error: FMU file '{fmu_path}' not found.[/red]")
        return None

    # Extract FMU content
    model_desc = fmpy.read_model_description(fmu_path)

    return model_desc
