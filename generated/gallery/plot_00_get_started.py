"""
A first example: an AC voltage source and a resistor
====================================================

This is a simple example of how to use CoFMPy to load a co-simulation system (JSON
configuration file and FMUs) and run the simulation.

The use case is a simple system with an AC voltage source and a resistor. The AC voltage
source generates a sinusoidal voltage signal, and the resistor consumes the power from
the source. The resistor has a variable resistance that can be changed during the
simulation.
"""

# %%
# We will first download all necessary ressources such as FMUs (source and resistor) and
# the configuration file from the public link provided below.
import os
import urllib.request
import zipfile

url = "https://share-is.pf.irt-saintexupery.com/s/39zaG9HkQWnePbi/download"

# Local path to ressources folder
ressources_path = "example1.zip"

# Download and unzip the file
urllib.request.urlretrieve(url, ressources_path)
with zipfile.ZipFile(ressources_path, "r") as zip_ref:
    zip_ref.extractall(".")

# Remove the zip file
os.remove(ressources_path)

print("Ressources unzipped in example1 folder!")

# %%
# Now that we have all the necessary ressources, we can start the example.
#
# The base object in CoFMPy is the [**Coordinator**](/api/coordinator). It manages all
# the components of CoFMPy: the Master algorithm, the graph engine, the data stream
# handlers, etc. In this tutorial, we only deal with the Coordinator that communicates
# for us.
#
# We will first import the Coordinator object from CoFMPy and create an instance of it.

from cofmpy import Coordinator

coordinator = Coordinator()

# %%
# ## The JSON configuration file
#
# The first step is to create the JSON configuration file based on your system. This
# file must contain the information about the FMUs, the connections between them, and
# the simulation settings. For more information, check the page on [how to create a JSON
# configuration file](/user_guide/configuration_file), see this page. The system also
# requires input data to run the simulation (here, the variable resistor from a CSV
# file).
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
# - The simulation settings: the loop solver and the edge separator (used in the graph
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
# example, you can access the loop solver of the co-simulation via the
# `master.loop_solver` attribute.

# We can check the list of FMUs in the Master or the loop solver used
print("FMUs in Master:", list(coordinator.master.fmu_handlers.keys()))
print(f"Loop solver: {coordinator.master.loop_solver}")

# ... and the stream handlers (here, the CSV source). Keys are (fmu_name, var_name)
print("\nCSV data stream handler key:", list(coordinator.stream_handlers.keys())[0])

csv_data_handler = coordinator.stream_handlers[("resistor", "R")]
print("CSV path for resistance value R:", csv_data_handler.path)
print("CSV data for R (as Pandas dataframe):\n", csv_data_handler.data.head())

# %%
# ## Running the simulation
#
# After loading the configuration file, you can run the simulation by calling the
# [`do_step` method](/api/coordinator/#cofmpy.coordinator.Coordinator.do_step). This
# method will run the simulation for a given time step via the Master algorithm.
#
# The `do_step` method will save the results in the data storages defined in the
# configuration file. You can access the data storages using the `data_storages`
# attribute of the Coordinator object. By default, a data storage for all outputs is
# created in the "storage/results.csv" file (see below).

print(f"Current time of the co-simulation: {coordinator.master.current_time}")

time_step = 0.05
coordinator.do_step(time_step)

print(
    "Current time of the co-simulation after one step: "
    f"{coordinator.master.current_time}"
)

# Run N steps
N = 30
for _ in range(N):
    coordinator.do_step(time_step)

print(
    f"Current time of the co-simulation after {N+1} steps: "
    f"{coordinator.master.current_time:.2f}"
)

# %%
# It is possible to run the simulation until a specific end time by using the
# [`run_simulation` method](/api/coordinator/#cofmpy.coordinator.Coordinator.run_simulation).
# This method will run the simulation until the end time and return the results of the
# simulation.
# TODO: Should we restart the simulation before running it? (init_simulation) or recreate
# the coordinator object?
end_time = 2.0

results = coordinator.run_simulation(time_step, end_time)
print(f"Current time of the co-simulation: {coordinator.master.current_time:.2f}")


# %%
# ## Visualizing the results
#
# The simulation results are stored in the data storages. You can access the results via
# the `data_storages` attribute of the Coordinator object.

print("Data storages:\n", coordinator.data_storages)

# %%
# You can visualize the results stored in the data storages.
#
# The default data storage is created for the results of the simulation: it stores the
# data for all outputs in a single CSV file. You can access the results via
# `coordinator.data_storages["results"]`.

default_storage = coordinator.data_storages["results"]
results = default_storage.load("results")
print(results.head(10))

# %%

results.plot(x="t")

# %%
# You can also visualize the graph of the system using the `plot_graph` method. This
# method will plot the connections between the FMUs in the system.

coordinator.graph_engine.plot_graph()
