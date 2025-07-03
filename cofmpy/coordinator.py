# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
"""
Coordinator class
"""

import pandas as pd

from .config_parser import ConfigParser
from .data_storage import BaseDataStorage
from .data_stream_handler import BaseDataStreamHandler
from .graph_engine import GraphEngine
from .master import Master


class Coordinator:
    """
    The **Coordinator** is the main class in CoFMPy. It controls the blocks internally
    in order to ease the usage of the library. For end users, this is the only interface
    to start with: from a JSON configuration file, the coordinator will instantiate and
    monitor all the required components.

    ```python
    from cofmpy import Coordinator

    # Instantiate the Coordinator
    my_coordinator = Coordinator()

    # Start the Coordinator (and all its components) from a JSON configuration file
    my_coordinator.start(conf_path="my_config_file.json")
    ```

    The Coordinator can then run the simulation using `do_step()` or `run_simulation()`.
    Internally, the Master component will execute the steps of the co-simulation.

    ```python
    n_steps = 100
    for _ in range(N):
        my_coordinator.do_step(step_size=0.05)
    ```

    It is then possible to get the simulation results as a Pandas dataframe :

    ```python
    results_df = my_coordinator.get_results()
    ```
    """

    def __init__(self):
        self.config_parser = None
        self.graph_engine = None
        self.master = None
        self.stream_handlers = None
        self.data_storages = None

        self.config_data = None

    def start(self, conf_path: str, fixed_point_init=False, fixed_point_kwargs=None):
        """
        Start the coordinator with the given configuration file.

        Args:
            conf_path (str): path to the configuration file.
            fixed_point_init (bool): whether to use the fixed-point initialization method.
            fixed_point_kwargs (dict): keyword arguments for the fixed point initialization
                method if fixed_point is set to True. Defaults to None, in which
                case the default values are used "solver": "fsolve",
                "time_step": minimum_default_step_size, and "xtol": 1e-5.
        """

        # 1. Start ConfigParser and parse the configuration file
        self.parse_config(conf_path)

        # print(self.config_parser.config_dict)

        # 2. Start GraphEngine
        self.start_graph_engine(self.config_parser.graph_config)

        # 3. Start Master
        self.config_parser.master_config["sequence_order"] = (
            self.graph_engine.sequence_order
        )
        self.start_master(
            self.config_parser.master_config,
            fixed_point_init=fixed_point_init,
            fixed_point_kwargs=fixed_point_kwargs,
        )

        # 4. Create DataStreamHandlers
        self.load_stream_handlers(self.config_parser.stream_handlers)

        # 5. Create DataStorages
        self.load_data_storages(self.config_parser.data_storages)

        # 6. Save all results in a CSV file (additional data storage)
        self.data_storages["results"] = BaseDataStorage.create_data_storage(
            {
                "type": "file",
                "config": {"output_dir": "./storage", "overwrite": True},
            }
        )
        # write the header for the results file
        output_names = []
        for fmu_id, outputs in self.master.get_outputs().items():
            for output_name in outputs:
                output_names.append(f"{fmu_id}.{output_name}")
        for stream in self.stream_handlers:
            output_names.append(f"{stream[0]}.{stream[1]}")
        self.data_storages["results"].save("results", [["t"] + output_names])

    def get_results(self) -> dict:
        """
        Get the results from the simulation.

        Returns:
            dict: dataframe with the results.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")
        return self.master.get_results()

    def parse_config(self, config_path: str):
        """
        Start the configuration parser to parse the given configuration file.

        Args:
            config_path (str): path to the configuration file
        """

        self.config_parser = ConfigParser(config_path)
        self.config_data = self.config_parser.config_dict

    def start_graph_engine(self, config: dict):
        """
        Start the graph engine with the given configuration.

        Args:
            config (dict): configuration for the graph engine containing the FMUs,
                connections, and edge separation.
        """
        self.graph_engine = GraphEngine(
            config["fmus"],
            config["symbolic_nodes"],
            config["connections"],
            config["edge_sep"],
        )

    def start_master(
        self, config: dict, fixed_point_init=False, fixed_point_kwargs=None
    ):
        """
        Start the master algorithm with the given configuration.

        Args:
            config (dict): configuration for the master algorithm containing the FMUs,
                connections, sequence order, and loop method.
            fixed_point_init (bool): whether to use the fixed-point initialization method.
            fixed_point_kwargs (dict): keyword arguments for the fixed point initialization
                method if fixed_point is set to True. Defaults to None, in which
                case the default values are used "solver": "fsolve",
                "time_step": minimum_default_step_size, and "xtol": 1e-5.
        """
        self.master = Master(
            fmu_config_list=config["fmus"],
            connections=config["connections"],
            sequence_order=config["sequence_order"],
            loop_solver=config["loop_solver"],
            fixed_point=fixed_point_init,
            fixed_point_kwargs=fixed_point_kwargs,
        )
        self.master.init_simulation(input_dict={})

    def load_stream_handlers(self, stream_handlers_config: dict):
        """
        Load the stream handlers from the given dictionary of configurations.

        Args:
            stream_handlers_config (dict): dictionary containing the configurations for
                the stream handlers.
        """
        self.stream_handlers = {
            key: BaseDataStreamHandler.create_handler(config)
            for key, config in stream_handlers_config.items()
        }

    def load_data_storages(self, data_storages_config: dict):
        """
        Load the data storages from the given dictionary of configurations.

        Args:
            data_storages_config (dict): dictionary containing the configurations for
                the data storages.
        """
        self.data_storages = {
            key: BaseDataStorage.create_data_storage(config)
            for key, config in data_storages_config.items()
        }

    def do_step(self, step_size: float, save_data=False):
        """
        Perform a simulation step.

        Args:
            step_size (float): simulation step size
            save_data (bool): whether to save the data in the default CSV data storage.
                Defaults to False.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        # Get data from inbound data stream handlers
        data = {
            key: handler.get_data(self.master.current_time)
            for key, handler in self.stream_handlers.items()
        }
        data_for_master = self._dict_tuple_to_dict_of_dict(data)

        # Do step in the master
        outputs = self.master.do_step(step_size, input_dict=data_for_master)

        # Save results and data
        if save_data:
            results = [self.master.current_time]
            for _, fmu_output_dict in outputs.items():
                for _, output_value in fmu_output_dict.items():
                    results.append(output_value[0])
            for d in data.values():
                results.append(d)
            self.data_storages["results"].save("results", [results])

        # Send data to outbound data stream handlers

    def run_simulation(self, step_size: float, end_time: float):
        """
        Run the simulation until the given end time.

        Args:
            step_size (float): simulation step size
            end_time (float): simulation end time
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        while self.master.current_time < end_time:
            self.do_step(step_size)

    def save_results(self, filename: str):
        """
        Save the results to a CSV file.

        Args:
            filename (str): name of the CSV file to save the results to.
        """
        df_results = pd.DataFrame.from_dict(self.get_results())

        # Sort the columns starting with "time" and then alphabetically
        columns = df_results.columns.tolist()
        columns.remove("time")
        columns = ["time"] + sorted(columns)

        # Set headers of the CSV file where tuple (fmu, var_name) is replaced by
        # "fmu.var_name"
        headers = list(columns)  # copy of the mutable list
        for i, col_header in enumerate(headers):
            if isinstance(col_header, tuple):
                headers[i] = f"{col_header[0]}.{col_header[1]}"

        df_results.to_csv(filename, columns=columns, header=headers, index=False)

    def _dict_tuple_to_dict_of_dict(self, dict_tuple: dict) -> dict:
        """
        Transforms a dictionary with tuples as keys to a dictionary of dictionaries.

        Args:
            dict_tuple (dict): dictionary with tuples as keys.

        Returns:
            dict: dictionary of dictionaries.
        """
        my_new_dict = {}
        for (var1, var2), obj in dict_tuple.items():
            if var1 not in my_new_dict:
                my_new_dict[var1] = {}
            my_new_dict[var1][var2] = [
                float(obj)
            ]  # must move the [float(obj)] to the data stream handler
        return my_new_dict

    def get_variable_names(self) -> list:
        """
        Get the names of all variables in the system.

        Returns:
            list: list of variable names as (fmu_id, var_name) tuples.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        var_names = []
        for fmu_id, fmu in self.master.fmu_handlers.items():
            var_names += [(fmu_id, var) for var in fmu.get_variable_names()]

        return var_names

    def get_variable(self, name: tuple) -> list:
        """
        Get the value of the given tuple fmu/variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            list: value of the variable, as a list.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        fmu_id, var_name = name
        return self.master.fmu_handlers[fmu_id].get_variable(var_name)

    def get_variables(self, names: list) -> dict:
        """
        Get the values of the given variables.

        Args:
            names (list): list of variable names as (fmu_id, var_name) to get,
                e.g. [("fmu1", "var3"), ("fmu2", "var1")].

        Returns:
            dict: dictionary with the variable names and their values.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        var_values = {}
        for name in names:
            var_values[name] = self.get_variable(name)

        return var_values

    def get_causality(self, name: tuple) -> str:
        """
        Gets the causality of the given variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            str: causality of the variable.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        fmu_id, var_name = name
        return self.master.fmu_handlers[fmu_id].get_causality(var_name)

    def get_variable_type(self, name: tuple) -> str:
        """
        Get the type of the given variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            str: type of the variable.
        """
        if self.master is None:
            raise RuntimeError("Coordinator not initialized. Call start() first.")

        fmu_id, var_name = name
        return self.master.fmu_handlers[fmu_id].get_variable_type(var_name)
