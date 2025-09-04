
from matplotlib import pyplot as plt
from cofmpy.coordinator import Coordinator
import pprint
from tqdm import tqdm
import os

coordinator = Coordinator()
config_path = "config_jacobi.json"
coordinator.start(config_path)

print("Input dict is :")
pprint.pp(coordinator.master._input_dict)
print("\nOutput dict is :")
pprint.pp(coordinator.master._output_dict)

print(coordinator.master.sequence_order)

# Force sequence order
coordinator.master.sequence_order = [{'programmer'}, ['controller', 'heater']]
print(coordinator.master.sequence_order)

communication_time_step = 0.01
coordinator.run_simulation(communication_time_step, 24)

results = coordinator.get_results()
coordinator.save_results("./results/results_cosim_heater_jacobi.csv")

# plot the results
import matplotlib.pyplot as plt

fig, axs = plt.subplots(5, 1, figsize=(10, 10), sharex=False)
fig.suptitle("Jacobi Simulation Results")

minLimit = 0
t = results["time"][minLimit:]
axs[0].plot(t, results[("programmer", "T_out")][minLimit:])
axs[0].plot(t, results[("heater", "T_out")][minLimit:])
axs[0].set_ylabel("T_out")
axs[0].set_title("T_out")
axs[0].legend(["Programmer", "Heater"])
axs[0].grid()

axs[1].plot(t, results[("controller", "P_out")][minLimit:])
axs[1].set_ylabel("P_out")
axs[1].set_title("P_out")
axs[1].legend(["Controller"])
axs[1].grid()

minLimit = 796
mnaxLimit = 806
t = results["time"][minLimit:mnaxLimit]
axs[2].plot(t, results[("programmer", "T_out")][minLimit:mnaxLimit], **{'marker': 'o'})
axs[2].set_ylabel("T_out")
axs[2].set_title("T_out")
axs[2].legend(["Programmer"])
axs[2].grid()

axs[3].plot(t, results[("controller", "P_out")][minLimit:mnaxLimit], **{'marker': 'o'})
axs[3].set_ylabel("P_out")
axs[3].set_title("P_out")
axs[3].legend(["Controller"])
axs[3].grid()

axs[4].plot(t, results[("heater", "T_out")][minLimit:mnaxLimit], **{'color': '#ff7f0e', 'marker': 'o'})
axs[4].set_ylabel("T_out")
axs[4].set_title("T_out")
axs[4].legend(["Heater"])
axs[4].grid()

plt.show()
