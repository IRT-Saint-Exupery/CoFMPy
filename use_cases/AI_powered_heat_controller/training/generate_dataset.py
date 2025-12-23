from collections import namedtuple

import matplotlib.pyplot as plt
import numpy as np

from cofmupy import Coordinator

default_config = {
    "fmus": [
        {"id": "controller", "path": "../fmus/HeatController.fmu"},
        {"id": "heater", "path": "../fmus/HeaterThermalModel.fmu"},
    ],
    "connections": [
        {
            "source": {"id": "controller", "variable": "P_out"},
            "target": {"id": "heater", "variable": "P_in"},
        }
    ],
}

step_size = 0.1
end_time = 500.0
N = int(end_time / step_size) + 1


def get_random_settings():
    """Generate random settings for the simulation.

    Random settings include:
    - heat_loss_nominal: float between 0.01 and 0.3, used as the base heat loss.
    - Kp (coefficient of the proportional controller): int between 10 and 50
    - Tobs_init (initial observed temperature): float between 0 and 30
    - Tc_series (setpoint temperature profile): piecewise constant array with random
      values between 10 and 30 and random change times between 200 and 1000 time steps
      apart.
    - heat_loss_series (heat loss profile): piecewise constant array with random
      values between 0.01 and 0.3, with random change times between 500 and 1000 time
      steps apart. Additionally, with a probability of 0.3, the heat loss is increased
      by heat_loss_nominal + 0.3 to simulate cut conditions.

    Returns:



    """

    heat_loss_nominal = np.random.uniform(0.01, 0.3)
    Kp = np.random.randint(10, 50)
    Tobs_init = np.random.uniform(0, 30)
    # Tc setpoint profile must be piecewise constant with random values between 15 and 25 and random change times at least 100 time steps apart
    change_times = [0]
    Tc_series = np.zeros(N)
    while change_times[-1] < N - 1:
        next_change = change_times[-1] + np.random.randint(200, 1000)
        if next_change < N - 1:
            change_times.append(next_change)
        else:
            change_times.append(N - 1)
    Tc_values = np.random.uniform(10, 30, size=len(change_times))
    for i in range(len(change_times) - 1):
        Tc_series[change_times[i] : change_times[i + 1]] = Tc_values[i]

    change_times = [0]
    heat_loss_series = np.zeros(N)
    while change_times[-1] < N - 1:
        next_change = change_times[-1] + np.random.randint(500, 1000)
        if next_change < N - 1:
            change_times.append(next_change)
        else:
            change_times.append(N - 1)
    heat_loss_values = np.random.uniform(0.01, 0.3, size=len(change_times))
    # random 0/1 values with probability 0.3 for 1, length of change_times
    above_nominal = np.random.choice([0, 1], size=len(change_times), p=[0.7, 0.3])
    for i in range(len(heat_loss_values)):
        if above_nominal[i] == 1:
            heat_loss_values[i] += heat_loss_nominal + 0.3
    for i in range(len(change_times) - 1):
        heat_loss_series[change_times[i] : change_times[i + 1]] = heat_loss_values[i]
    cut_series = heat_loss_series > heat_loss_nominal + 0.3

    Settings = namedtuple(
        "Settings",
        [
            "heat_loss_nominal",
            "Kp",
            "Tobs_init",
            "Tc_series",
            "heat_loss_series",
            "cut_series",
        ],
    )
    return Settings(
        heat_loss_nominal, Kp, Tobs_init, Tc_series, heat_loss_series, cut_series
    )


def run_simulation(settings):
    coordinator = Coordinator()
    coordinator.start(default_config)

    coordinator.set_variable(("controller", "Kp"), [settings.Kp])

    next_Tobs = [settings.Tobs_init]
    for step_idx in range(N):
        coordinator.set_variable(
            ("heater", "nominal_heat_loss"), [settings.heat_loss_series[step_idx]]
        )
        coordinator.master.set_inputs(
            {
                "controller": {
                    "Tc": [settings.Tc_series[step_idx]],
                    "T_in": next_Tobs,
                },
                "heater": {"T_in": next_Tobs},
            },
        )
        coordinator.do_step(step_size, save_data=True)
        next_Tobs = coordinator.get_variable(("heater", "T_out"))

    return coordinator.get_results()


def aggregate_data(settings, results):
    """Aggregate simulation data into a structured format.

    Args:
        settings: The settings used for the simulation.
        results: The results obtained from the simulation.

    Returns:
        A dictionary containing aggregated data.
    """
    Tobs = np.array([settings.Tobs_init] + results[("heater", "T_out")][:-1])
    Tpred = np.array(results[("heater", "T_out")])

    data = {
        "time": results["time"],
        "Tobs": Tobs,
        "Tpred": Tpred,
        "P_out": results[("controller", "P_out")],
        "Tc_series": settings.Tc_series,
        "heat_loss_series": settings.heat_loss_series,
        "cut_series": settings.cut_series,
        "heat_loss_nominal": settings.heat_loss_nominal,
        "Kp": settings.Kp,
        "Tobs_init": settings.Tobs_init,
    }
    return data


# print("Settings:")
# print("- Nominal heat loss:", heat_loss_nominal)
# print("- Initial observed temp:", Tobs_init)
# print("- Controller Kp:", Kp)


# Get random settings
settings = get_random_settings()

# Run simulation
results = run_simulation(settings)
print("Simulation completed.")

# coordinator = Coordinator()
# coordinator.start(default_config)

# coordinator.set_variable(("controller", "Kp"), [settings.Kp])
# Tobs_series = np.zeros(N)
# Tobs_series[0] = settings.Tobs_init

# next_Tobs = settings.Tobs_init
# for step_idx in range(N - 1):
#     coordinator.set_variable(
#         ("heater", "nominal_heat_loss"), [settings.heat_loss_series[step_idx]]
#     )
#     coordinator.master.set_inputs(
#         {
#             "controller": {
#                 "Tc": [settings.Tc_series[step_idx]],
#                 "T_in": [next_Tobs],
#             },
#             "heater": {"T_in": [next_Tobs]},
#         },
#     )
#     coordinator.do_step(step_size, save_data=True)
#     next_Tobs = coordinator.get_variable(("heater", "T_out"))[0]


# print("Simulation completed.")
# results = coordinator.get_results()

data = aggregate_data(settings, results)

print(data["Tobs"])
print(data["Tpred"])


# Plot results
fig, axs = plt.subplots(2)
axs[0].plot(results["time"], results[("heater", "T_out")], label="Heater Output Temp")
axs[0].plot(
    results["time"],
    0.3 * np.array(results[("controller", "P_out")]),
    label="Controller Output Power",
    linestyle="--",
)
axs[0].plot(
    results["time"], settings.Tc_series, label="Setpoint Temp", linestyle="--"
)
axs[0].grid()

axs[1].plot(results["time"], settings.heat_loss_series, label="Heat Loss")
axs[1].plot(
    results["time"],
    settings.cut_series * (settings.heat_loss_nominal + 0.3),
    label="Cut heat",
    linestyle=":",
)
axs[1].hlines(
    [settings.heat_loss_nominal, settings.heat_loss_nominal + 0.3],
    0,
    end_time,
    linestyle="--",
)
axs[1].grid()

plt.savefig("heater_output_temp.png")
