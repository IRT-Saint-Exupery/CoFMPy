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
A first example: an AC voltage source and a resistor
====================================================

This is a simple example of how to use CoFmuPy to load a co-simulation system (JSON
configuration file and FMUs) and run the simulation.

The use case is a simple system with an AC voltage source and a resistor. The AC voltage
source generates a sinusoidal voltage signal, and the resistor consumes the power from
the source. The resistor has a variable resistance that can be changed during the
simulation.

![source resistor system](../../assets/source_resistor.png)

"""
# %%
# We will first download all necessary resources such as the FMUs (source and resistor)
# and the configuration file from the public link provided below.
import os
import urllib.request
import zipfile

url = "https://share-is.pf.irt-saintexupery.com/s/HSNSeteJPoJjyXx/download"

# Local path to resources folder
resources_path = "example1.zip"

# Download and unzip the file
urllib.request.urlretrieve(url, resources_path)
with zipfile.ZipFile(resources_path, "r") as zip_ref:
    zip_ref.extractall(".")

# Remove the zip file
os.remove(resources_path)

print("Resources unzipped in example1 folder!")

# %%
# Now that we have all the necessary resources, we can start the example.
#
# The base object in CoFmuPy is the [**Coordinator**](../../api/coordinator.md). It
# manages all the components of CoFmuPy: the Master algorithm, the graph engine, the data
# stream handlers, etc. In this tutorial, we only deal with the Coordinator that
# communicates automatically with the different components.
#
# We will first import the Coordinator object from CoFmuPy and create an instance of it.

from cofmupy import Coordinator

coordinator = Coordinator()

# %%
# ## The JSON configuration file
#
# The first step is to create the JSON configuration file based on your simulation
# system. This file must contain the information about the FMUs, the connections between
# them, and the simulation settings. For more information, check the page on [how to
# create a JSON configuration file](../../user_guide/configuration_file.md), see this
# page. The system also requires input data to run the simulation (here, the variable
# resistor from a CSV file).
#
# Here is the content of the configuration file for this example:

config_path = "example1/config_with_csv.json"
with open(config_path, "r") as f:
    print(f.read())

# %%
# In the JSON configuration file, you can see the following information:
#
# - The 2 FMUs used in the system: an AC voltage source and a resistor
# - 2 connections:
#     - the output of the source is connected to the input of the resistor
#     - the resistance value of the resistor is set by a CSV file
# - The simulation settings: the cosimulation method and the edge separator (used in the graph
#   visualization).
#
# The next step is to load the configuration file via the Coordinator. This will start
# the multiple components to handle the whole simulation process:
#
# - the Master: the main process that controls the co-simulation
# - the data stream handlers: the objects that read and write data from/to the system
# - the graph engine

coordinator.start(config_path)

# %%
# You can access the attributes of the components of the Coordinator object. For
# example, you can access the co-simulation method via the
# `master.cosim_method` attribute.

# We can check the list of FMUs in the Master or the cosimulation method used
print("FMUs in Master:", list(coordinator.master.fmu_handlers.keys()))
print(f"Cosimulation method: {coordinator.master.cosim_method}")

# ... and the stream handlers (here, the CSV source). Keys are (fmu_name, var_name)
print("\nCSV data stream handler key:", coordinator.stream_handlers[0])

csv_data_handler = coordinator.stream_handlers[0]
print("CSV path for resistance value R:", csv_data_handler.path)
print("CSV data for R (as Pandas dataframe):\n", csv_data_handler.data.head())

# %%
# You can also visualize the graph of the system using the `plot_graph` method. This
# method will plot the connections between the FMUs in the system.

coordinator.graph_engine.plot_graph()

# %%
# ## Running the simulation
#
# After loading the configuration file, you can run the simulation by calling the
# [`do_step` method](../../api/coordinator.md#cofmupy.coordinator.Coordinator.do_step).
# This method will run the simulation for a given time step via the Master algorithm.
#
# The `do_step` method will save the results in the data storages defined in the
# configuration file. You can access the data storages using the `data_storages`
# attribute of the Coordinator object. By default, a data storage for all outputs is
# created in the "storage/results.csv" file (see below).

print(f"Current time of the co-simulation: {coordinator.master.current_time}")

time_step = 0.01
coordinator.do_step(time_step)

print(
    "Current time of the co-simulation after one step: "
    f"{coordinator.master.current_time}"
)

# Run N steps
N = 100
for _ in range(N):
    coordinator.do_step(time_step)

print(
    f"Current time of the co-simulation after {N+1} steps: "
    f"{coordinator.master.current_time:.2f}"
)

# %%
# It is possible to run the simulation until a specific end time by using the
# [`run_simulation`
# method](../../api/coordinator.md#cofmupy.coordinator.Coordinator.run_simulation). This
# method will run the simulation until the end time and return the results of the
# simulation. Note that you should recreate a new Coordinator from scratch. It is not
# possible to mix both `do_step` and `run_simulation` methods in the same Coordinator
# object.
#
# At the end of the simulation, you can also manually save results to a CSV file:

coordinator.save_results("simulation_results.csv")

# %%
# ## Visualizing the results
#
# Results can be accessible directly in the Master object or in the CSV file we just
# saved.

import pandas as pd

results = pd.read_csv("simulation_results.csv")
print(results.head(10))

# %%

results.plot(x="time", grid=True)


# %%
# We can observe that the change of resistance value at t = 0.42s effectively changes
# the current $I = U/R$ flowing through the resistor.
