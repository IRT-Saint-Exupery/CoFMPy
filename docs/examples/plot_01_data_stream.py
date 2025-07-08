"""
Understanding the data stream handlers
======================================

This is a simple example to illustrate the data stream handlers in CoFMPy. It shows how
to use the `LiteralDataStreamHandler` and `CSVDataStreamHandler` to modify the input
data of an FMU during the simulation. The FMU variables of causality `input` or
`parameter` can be set during the co-simulation using data streams.

The use case is the famous *Bouncing Ball* FMU that simulates a ball bouncing on the
ground. Here, we will change the coefficient of restitution (`e`) during the simulation,
i.e. how high the ball bounces after touching the ground.

Here, we do not consider co-simulation with multiple FMUs and algebraic loops. We focus
on the usage of data stream handlers.

!!! note
    For more details on how to describe data streams in the JSON configuration file,
    please read the [corresponding page](../../user_guide/configuration_file.md) in the
    User Guide.

"""

# %%
# # The original bouncing ball example
#
# As as baseline, we will load and run the simulation of the Bouncing Ball FMU without
# any data stream handler. This will give us a reference for the simulation results.
#
# First, let's define the configuration for the Bouncing Ball system. Instead of using
# a JSON file, we will directly create the FMU and the handlers in a Python dictionary.

from cofmpy import Coordinator

# We define a simple CoFMPy config dictionary with a single FMU and no connection
config = {"fmus": [{"id": "bouncing_ball", "path": "fmus/BouncingBall.fmu"}]}

# We create a Coordinator object and start it with the config dictionary
coordinator = Coordinator()
coordinator.start(config)

e = coordinator.get_variable(("bouncing_ball", "e"))
print("Original value of coefficient of restitution 'e' (from the FMU):", e)

# %%

# We now run the simulation for 2.8 seconds and retrieve the results
coordinator.run_simulation(step_size=0.01, end_time=2.8)
results = coordinator.get_results()

# %%
import matplotlib.pyplot as plt


def plot_height(results):
    plt.plot(results["time"], results[("bouncing_ball", "h")])
    plt.grid()
    plt.title("Bouncing Ball Height over time")
    plt.xlabel("Time [s]")
    plt.ylabel("Height [m]")


plot_height(results)


# %%
# # The Literal data stream handler
#
# The Literal data stream handler is the simplest data handler. It can be used when an
# input or parameter of an FMU changes a few times during the simulation. These changes
# are directly described in the configuration as below: a connection is defined where
# the source is the literal values and the target is the variable `e` of the FMU.
#
# Here, we start with a coefficient of restitution `e` of 0.7, and at time t=1.0s, we
# change it to 0.5.

config = {
    "fmus": [{"id": "bouncing_ball", "path": "fmus/BouncingBall.fmu"}],
    "connections": [
        {
            "source": {"type": "literal", "values": {"0": 0.7, "1.0": 0.5}},
            "target": {"id": "bouncing_ball", "variable": "e"},
        }
    ],
}

# %%
coordinator = Coordinator()
coordinator.start(config)

coordinator.run_simulation(step_size=0.01, end_time=2.8)

results = coordinator.get_results()
plot_height(results)

# %%
# We observe that from t = 1s, the ball bounces less high than in the reference
# simulation because the coefficient of restitution was set to 0.5.

# %%
# # The CSV data stream handler
#
# The CSV data stream handler is recommended when the input or parameter of an FMU
# changes continuously during the simulation. The values are defined in a CSV file. The
# CSV file should have at least two columns, one for the time and one for the value of
# the input/parameter we want to set. The name of the time column must be "t".

# We create a CSV file with two columns. The time column must be named "t"
text = """
t,restitution_coef
0.0,0.7
1.0,0.5
1.2,0.9
"""
with open("restitution_schedule.csv", "w") as f:
    f.write(text)


# %%
# Now, we can define the configuration for the Bouncing Ball system with the CSV file.
# Note that the `variable` name in the `source` dictionary must match the name of the
# column in the CSV file, here "restitution_coef".

config = {
    "fmus": [{"id": "bouncing_ball", "path": "fmus/BouncingBall.fmu"}],
    "connections": [
        {
            "source": {
                "type": "csv",
                "path": "restitution_schedule.csv",  # CSV filepath
                "variable": "restitution_coef",  # Name of the column in the CSV file
            },
            "target": {"id": "bouncing_ball", "variable": "e"},
        }
    ],
}

# %%
coordinator = Coordinator()
coordinator.start(config)

coordinator.run_simulation(step_size=0.01, end_time=2.8)

results = coordinator.get_results()
plot_height(results)

# %%
# # Going further with data stream handlers
#
# ### Interpolation
#
# All data stream handlers have an `interpolation` parameter that is set to `previous`
# by default. This means that the value of the input/parameter variable is set to the
# last value before the current time step. You can change this to `linear` to use
# linear interpolation between the values in the CSV file. This is useful when the
# input/parameter variable changes continuously during the simulation.

config = {
    "fmus": [{"id": "bouncing_ball", "path": "fmus/BouncingBall.fmu"}],
    "connections": [
        {
            "source": {
                "type": "literal",
                "values": {"0": 0.7, "2.5": 0.3},
                "interpolation": "linear",
            },
            "target": {"id": "bouncing_ball", "variable": "e"},
        }
    ],
}

coordinator = Coordinator()
coordinator.start(config)

coordinator.run_simulation(step_size=0.01, end_time=2.8)
results = coordinator.get_results()
plot_height(results)

# %%
# ### Kafka data stream handler
#
# The Kafka data stream handler is used to read data from a Kafka topic. This is useful
# for real-time data streaming. The configuration for the Kafka data stream handler is
# similar to the CSV data stream handler, but you need to specify the Kafka topic and
# the server address.
#
# Here is an example of a Kafka data stream handler configuration:

config = {
    "fmus": [{"id": "bouncing_ball", "path": "fmus/BouncingBall.fmu"}],
    "connections": [
        {
            "source": {
                "type": "kafka",
                "uri": "localhost:9092",
                "group_id": "my_group",
                "topic": "my_topic",
                "variable": "my_variable_name_for_e",
            },
            "target": {"id": "bouncing_ball", "variable": "e"},
        }
    ],
}
# %%
# # Conclusion
#
# This example shows how to use the data stream handlers (`Literal` and `CSV`) to
# modify FMU inputs or parameters dynamically during a simulation. In the Bouncing Ball
# example, the change in the coefficient of restitution affects the bounce height,
# illustrating runtime parameter flexibility.
