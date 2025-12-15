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
A follow-up example: mixing an FMU with a Python proxy FMU
==========================================================

This tutorial is a continuation of the "A first example: an AC voltage source and a resistor".
The goal here is to show how **CoFmuPy** allows you to mix **compiled FMUs** and
**Python proxy FMUs** (`fmuproxy`) in the same co-simulation.

- The AC voltage source is provided as a compiled FMU (`source.fmu`)
- The resistor is defined as a Python proxy FMU (`resistor.py`)

This setup illustrates a common workflow:
you can rapidly prototype some parts of your system in Python (for example to test an
AI model or a simple block), while keeping others as standard FMUs.
"""

# %%
# ## Downloading and preparing resources
#
# As before, we first download the resources (the FMU and the Python proxy file)
# from a shared repository and unzip them locally.

import os
import urllib.request
import zipfile

url = "https://share-is.pf.irt-saintexupery.com/s/HSNSeteJPoJjyXx/download"
resources_path = "example1.zip"

urllib.request.urlretrieve(url, resources_path)
with zipfile.ZipFile(resources_path, "r") as zip_ref:
    zip_ref.extractall(".")
os.remove(resources_path)

print("Resources unzipped in example1 folder!")

# %%
# ## Creating the Coordinator
#
# As in the previous tutorial, the base object is the `Coordinator`.
# It manages the master algorithm, the FMUs, the proxies, the data handlers, etc.

from cofmupy import Coordinator

coordinator = Coordinator()

# %%
# ## The JSON configuration file
#
# The configuration file describes the system:
# - one FMU (`source.fmu`) for the AC voltage source
# - one Python proxy (`resistor.py`) implementing a resistor
# - the connection between the source output and the resistor input
#
# Let’s open the configuration file to inspect it.

config_path = "example1/config_with_fmu_proxy.json"
with open(config_path, "r") as f:
    print(f.read())

# %%
# ## Starting the simulation system
#
# The coordinator loads the FMUs and proxies, starts the services, and prepares the simulation.

coordinator.start(config_path)

# %%
# Once loaded, we can inspect the FMUs/proxies and the cosimulation method used.

print("FMUs and proxies in Master:", list(coordinator.master.fmu_handlers.keys()))
print(f"Cosimulation method: {coordinator.master.cosim_method}")

# %%
# ## Running the simulation step by step
#
# Just like before, we can step through the simulation manually.

print(f"Initial simulation time: {coordinator.master.current_time}")

time_step = 0.01
coordinator.do_step(time_step)

print(f"Simulation time after one step: {coordinator.master.current_time}")

# Run N steps
N = 100
for _ in range(N):
    coordinator.do_step(time_step)

print(f"Simulation time after {N+1} steps: {coordinator.master.current_time:.2f}")

# %%
# ## Running the full simulation
#
# Alternatively, we can run until a specific end time in one command.

coordinator.save_results("simulation_results.csv")

# %%
# ## Visualizing results
#
# Results are stored in a CSV file. We can load them into pandas and plot.

import pandas as pd

results = pd.read_csv("simulation_results.csv")
print(results.head(10))
# Results can be accessible directly in the Master object or in the CSV file we just
# saved.

# %%

results.plot(x="time", grid=True)

# %%
# ## Conclusion
#
# This example shows how easy it is to integrate a Python proxy FMU (`fmuproxy`)
# alongside compiled FMUs in CoFmuPy.
#
# This workflow is ideal when:
# - you want to test new logic (e.g., AI model) quickly in Python
# - you don’t want to package everything as an FMU yet
# - you still need interoperability with other FMUs
#
# Later, the Python proxy can be exported as a true FMU (using `PythonFMU` for example),
# making the system fully portable across different tools.
