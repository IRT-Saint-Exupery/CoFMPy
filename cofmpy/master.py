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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Module for managing and executing co-simulations involving multiple FMUs.

This module provides a `Master` class that handles FMU initialization, input setting,
stepping, and result collection during simulation.

"""
from collections import defaultdict

import numpy as np

from .utils import FixedPointInitializer
from .wrappers import FmuHandlerFactory
import copy

from OMSimulator import SSP, CRef, Settings, FMU


class Master:
    """
    Manages and executes the co-simulation involving multiple FMUs.

    Attributes:
        fmu_config_list (list):
            A list of dictionaries containing information about the FMUs to be used in
            the simulation.
        connections (dict):
            A dictionary of connections between FMUs. The keys are tuples (source_fmu,
            source_variable), and the values are dictionaries with information about the
            source and target FMUs and variables.
        sequence_order (list):
            The order in which FMUs should be executed.
        cosim_method (str):
            The method used to solve algebraic loops in the simulation.
        current_time (float):
            The current simulation time.
        fixed_point (bool):
            Whether to use the fixed-point initialization method.
        fixed_point_kwargs (dict):
            Keyword arguments for the fixed-point initialization method.

    Methods:
        __init__(fmu_config_list, connections, sequence_order, cosim_method="jacobi",
            fixed_point=False, fixed_point_kwargs=None):
            Initializes the Master class with the given FMU list, connection list,
            sequence order, and algebraic loop solver.

        sanity_check():
            Checks FMU compatibility, I/Os, and headers with the corresponding
            algorithm.

        set_inputs(input_dict=None):
            Sets the input values for the current simulation step using the provided
            input dictionary.

        init_simulation(input_dict=None):
            Initializes the simulation environment and FMUs.

        get_outputs() -> dict[str, list]:
            Returns the output dictionary for the current step.

        get_results():
            Returns the results of the simulation.

        solve_loop(fmu_ids, step_size, algo="jacobi"):
            Uses the defined algorithm to solve algebraic loops in the simulation.

        do_step(step_size, input_dict=None, record_outputs=True):
            Performs a single step of the simulation, updating inputs, executing FMUs,
            and propagating outputs.
    """

    # pylint: disable=too-many-instance-attributes

    __keys = {
        "fmus": "FMUs",
        "id": "id",
        "path": "path",
        "init": "initialization",
        "step_t": "steptime",
        "suppl": "supplier",
        "conn": "connections",
        "src_fmu": "source_fmu",
        "src_var": "source_variable",
        "src_unit": "source_unit",
        "tgt_fmu": "target_fmu",
        "tgt_var": "target_variable",
        "tgt_unit": "target_unit",
    }

    def __init__(
        self,
        fmu_config_list: list,
        connections: dict,
        sequence_order: list,
        cosim_method: str = "jacobi",
        iterative: bool = False,
        fixed_point=False,
        fixed_point_kwargs=None,
    ):
        """
        Initializes the Master class with FMU configurations, connection details,
        sequence order, and loop solver.

        Args:
            fmu_config_list (list): List of dictionaries with FMU configurations.
            connections (dict): Dictionary mapping connections between FMUs.
            sequence_order (list): Execution order of FMUs.
            cosim_method (str, optional): Strategy for coordinating FMUs in
                co-simulation. Options are "jacobi" and "gauss-seidel".
                Defaults to "jacobi".
            iterative (str, optional): Whether to solve algebraic loops iteratively.
                Defaults to False.
            fixed_point (bool): whether to use the fixed-point initialization method.
            fixed_point_kwargs (dict): keyword arguments for the fixed point
            initialization
                method if fixed_point is set to True. Defaults to None, in which
                case the default values are used "solver": "fsolve",
                "time_step": minimum_default_step_size, and "xtol": 1e-5.
        """

        self.fmu_config_list = fmu_config_list  # List of FMU configurations (dict) from config file
        self.connections = connections  # Dict of connections between FMUs

        # Cosimulation method (default: Jacobi)
        self.cosim_method = cosim_method
        # Whether iterative method requested (default: False)
        self.iterative = iterative

        # Load FMUs into dict of FMU Handlers
        self.fmu_handlers = {}
        self.model = SSP()
        self._add_fmus_to_ssp()
        self._add_connections_to_ssp()
        self.model.list()
        self.model = self.model.instantiate()

        # Check if the names of the variables match between the connection dict and
        # the FMUs
        # self._check_connections()

        # Sequence order of execution as a List of FMU IDs. Extracted by config
        # parser module
        # Sequence order of execution as a List of FMU IDs. Extracted by config parser
        # self.sequence_order = sequence_order
        # if self.sequence_order is None:
        #     self.sequence_order = [d[self.__keys["id"]] for d in self.fmu_config_list]

        # init current_time to None to check if init_simulation() has been called
        self.current_time = None
        # Init output and input dictionaries for FMUs to maintain state between steps
        # Initialize arrays for inputs and outputs
        # self._input_dict = {fmu_id: np.zeros(len(fmu.get_input_names())) for fmu_id, fmu in self.fmu_handlers.items()}

        # self._output_dict = {
        #     fmu_id: np.zeros(len(fmu.get_output_names())) for fmu_id, fmu in self.fmu_handlers.items()
        # }
        # Results dictionary to store the output values for each step
        self._results = defaultdict(list)

    def sanity_check(self):  # TODO
        """
        Checks the compatibility of FMUs, including input/output validation and
        algorithm compliance.
        """
        self._check_connections()

    def _check_connections(self):
        """
        Checks whether the variable names in connections match the actual
        variable names in the FMUs and verifies that the source variable is an 'output'
        and the target variable is an 'input' (if causality is specified).

        Raises:
            ValueError: If a variable name does not exist in the respective FMU.
            ValueError: If the source variable is not an 'output' or the target variable
                is not an 'input'.
        """
        for (source_fmu, source_var), targets in self.connections.items():

            # Check if source variable exists in source FMU output list
            if source_var not in self.fmu_handlers[source_fmu].get_output_names():
                raise ValueError(
                    f"Source variable '{source_var}' not found in outputs of "
                    f"FMU '{source_fmu}': "
                    f"{self.fmu_handlers[source_fmu].get_output_names()}"
                )

            for target_fmu, target_var in targets:
                # Check if target variable exists in target FMU input list
                if target_var not in self.fmu_handlers[target_fmu].get_input_names():
                    raise ValueError(
                        f"Target variable '{target_var}' not found in inputs of "
                        f"FMU '{target_fmu}': "
                        f"{self.fmu_handlers[target_fmu].get_input_names()}"
                    )

    def _add_fmus_to_ssp(self):
        """ """
        for fmu_info_dict in self.fmu_config_list:
            fmu_id = fmu_info_dict["id"]
            fmu_path = fmu_info_dict["path"]
            print("Adding FMU to SSP:", fmu_id, fmu_path)
            self.fmu_handlers[fmu_id] = FMU(fmu_path)
            resource_name = "resource/" + fmu_id + ".fmu"
            self.model.addResource(fmu_path, resource_name)
            self.model.addComponent(CRef("default", fmu_id), resource_name)

    def _add_connections_to_ssp(self):
        """ """
        for (source_fmu, source_var), targets in self.connections.items():
            for target_fmu, target_var in targets:
                self.model.addConnection(
                    CRef("default", source_fmu, source_var),
                    CRef("default", target_fmu, target_var),
                )

    def initialize_values_from_config(self):
        """
        Initializes the FMU variables (inputs/outputs/parameters) with the values
        provided in the configuration dict.

        If the variable is an input, it is also added to the input dictionary
        """
        if self.current_time is None:
            raise RuntimeError("Current time is not initialized. Call init_simulation() first.")

        for fmu_config in self.fmu_config_list:
            init_values = fmu_config["initialization"]
            for key, value in init_values.items():
                print("DEBUG - setting initial value:", fmu_config["id"], key, value)
                self.model.setValue(CRef("default", fmu_config["id"], key), value)

    def set_inputs(self, input_dict=None):
        """
        Sets the input values for the current simulation step.

        This method populates the internal input dictionary (`self._input_dict`) with
        values for the current step. It updates these values with those provided in the
        `input_dict` parameter, if given. The `input_dict` parameter is expected to be
        a dictionary of dictionaries, where each key is an FMU identifier and each value
        is another dictionary mapping variable names to their respective values (e.g.,
        {"FMU1": {"var1": value}, "FMU2": {"var2": val, "var3": val}}).

        Args:
            input_dict (dict, optional): A dictionary of dictionaries containing input
                values to override the initialization values. Defaults to None.

        Raises:
            RuntimeError: If the current simulation time (`self.current_time`) is not
                initialized. Ensure that init_simulation()` is called before invoking
                this method.
        """
        if self.current_time is None:
            raise RuntimeError("Current time is not initialized. Call init_simulation() first.")

        if input_dict is None:
            return

        for fmu_id, vars in input_dict.items():
            for var_name, value in vars.items():
                print("DEBUG - setting input value:", fmu_id, var_name, value[0])
                self.model.setValue(CRef("default", fmu_id, var_name), value[0])

    def get_input_dict(self) -> dict:
        """
        Returns the input dictionary for the current step.

        Returns:
            dict: A dictionary containing the input values for the current step,
                structured as `[fmu_id][variable_name] => list(value)`.
        """
        return self._input_dict

    def init_simulation(self, input_dict=None):
        """
        Initializes the simulation environment and FMUs.

        This method sets up the necessary dictionaries for the simulation and
        initializes the FMUs with either a fixed point algorithm or values provided in
        the input dictionary.

        Args:
            input_dict (dict): A dictionary containing input values for the simulation.
                Defaults to None.

        The method performs the following steps:
            1. Sets the current simulation time to 0.
            2. If fixed_point is True, calls the _fixed_point_init() method.
            3. Otherwise, sets the inputs using the provided input_dict and initializes
                each FMU with these values.

        **Note**: The FMUs are reset after setting the initial values.
        """

        # # Init output and input dictionaries
        # for fmu_id, fmu in self.fmu_handlers.items():
        #     self._output_dict[fmu_id] = {key: [0] for key in fmu.get_output_names()}
        #     self._input_dict[fmu_id] = {key: [0] for key in fmu.get_input_names()}

        # Init current_time of simulation to 0
        self.current_time = 0.0

        # Init input/output/parameter variables with the values provided in the config
        self.initialize_values_from_config()

        print("DEBUG model.initialize() called")
        self.model.initialize()

        self.model.simulate()

    def get_outputs(self) -> dict[str, list]:
        """
        Returns the output dictionary for the current step.

        Returns:
            dict: A dictionary containing the output values of the current step,
                structured as `[FMU_ID][Var]`.
        """
        output_dict = {}
        for fmu_id, fmu in self.fmu_handlers.items():
            output_dict[fmu_id] = {}
            for var in fmu.variables:
                if var.causality.name == "output":
                    output_dict[fmu_id][str(var.name)] = self.model.getValue(CRef("default", fmu_id, var.name))
        print("DEBUG get_outputs:", output_dict)
        return output_dict

    def get_results(self) -> dict:
        """
        Returns the results of the simulation, this includes the values of every output
        variables, for each step, up until the current time of simulation.

        Returns:
            dict: A dictionnary containing output values of every step, structured as
                [(FMU_ID, Var)]

        """
        return self._results

    def solve_loop(self, fmu_ids, step_size: float, algo="jacobi", iterative=False) -> dict:
        """
        Performs a single simulation step on the given FMUs, using the defined algorithm
        to solve algebraic loops in the simulation.

        In the case there is no loop, the function will propagate the output values and
        return them.

        Args:
            fmu_ids (list[str]): List of highly coupled FMUs. Contains only one FMU if
                there is no loop.
            step_size (float): The step size for **data exchange** (in cosimulation
                mode, FMU integration step is fixed).
            algo (str): The algorithm to use to solve the loop (default: "jacobi").
            iterative (bool): Whether iterative method requested to solve the loop.

        Returns:
            dict: A dictionary containing the output values for this step of the FMUs
                given, structured as `[FMU_ID][Var]`

        """

        # Verify algo is a known algo name
        if algo not in ("jacobi", "gauss_seidel"):
            raise NotImplementedError(f"Algorithm {algo} not implemented for loop solving.")

        outputs = {}  # key: fmu_id, value: output_dict (var_name, value)
        # Copy useful inputs to local "inputs" variable
        inputs = {fmu_id: self._input_dict[fmu_id] for fmu_id in fmu_ids}

        current_iteration = 0
        tol = 1e-3
        max_iteration = 10
        converged = False
        fmu_states = defaultdict(list)  # variable for state storage for each FMU

        while not converged and current_iteration < max_iteration:
            # Save inputs for check coherence
            inputs_before = copy.deepcopy(inputs)
            for fmu_id in fmu_ids:
                fmu = self.fmu_handlers[fmu_id]

                if iterative:
                    if fmu_id in fmu_states:  # If state exists => retrieve state
                        fmu.set_state(fmu_states[fmu_id])
                    else:  # Save state
                        fmu_states[fmu_id] = fmu.get_state()

                outputs[fmu_id] = fmu.step(self.current_time, step_size, inputs[fmu_id])

                # Update inputs into fmu loop, only for gauss-seidel algo
                if algo == "gauss_seidel":
                    self.apply_fmu_outputs_to_inputs(inputs, fmu_id, outputs[fmu_id])

            # Update inputs at the end of fmu loop, only for Jacobi algo
            if algo == "jacobi":
                for fmu_id in fmu_ids:
                    self.apply_fmu_outputs_to_inputs(inputs, fmu_id, outputs[fmu_id])

            # Exit loop if not iterative or only 1 FMU inside loop
            if not iterative or len(fmu_ids) == 1:
                break

            conv_val = True
            residuals = self.get_residual(inputs_before, outputs)
            for fmu_id, residual in residuals.items():
                conv_val = conv_val and residual < tol

            converged = conv_val
            current_iteration += 1

        """
        if iterative and len(fmu_ids) != 1:
            if current_iteration == max_iteration:
                print(
                    str(self.current_time)
                    + " - Max iteration reached with following solution "
                    + str(output)
                )
            else:
                print(
                    str(self.current_time)
                    + " - Convergence found "
                    + str(current_iteration)
                    + " iterations"
                )
        """
        return outputs

    def do_fixed_point_step(self, step_size: float, input_dict=None):
        """
        This method updates the input dictionary with the values from the provided input
        dictionary, performs a single step of the simulation on each FMU, using the
        default jacobi method, propagates the output values to the corresponding
        variables for the next step, and updates the current simulation time accordingly. It also
        stores the output values in the results dictionary.

        Args:
            step_size (float): The size of the simulation step.
            input_dict (dict, optional): A dictionary containing input values for the
                simulation. Defaults to None.
            record_outputs (bool, optional): Whether to store the output values in the
                results dictionary. Defaults to True.

        Returns:
            dict: A dictionary containing the output values for this step, structured as
                `[FMU_ID][Var]`.

        """
        self.set_inputs(input_dict=input_dict)
        for fmu_ids in self.sequence_order:
            # out is fill with key: fmu_id, value: output_dict (var_name, value)
            out = self.solve_loop(fmu_ids, step_size)

            for fmu_id, fmu_output_dict in out.items():
                for output_name, value in fmu_output_dict.items():

                    # add each output to the output dict, [FMU_ID][Var] as key
                    self._output_dict[fmu_id][output_name] = value

        # update 1 for all inputs with outputs
        for fmu_id, fmu_output_dict in self._output_dict.items():
            self.apply_fmu_outputs_to_inputs(self._input_dict, fmu_id, fmu_output_dict)
        self.current_time += step_size
        # Return the output value for this step
        return self._output_dict

    def do_step(self, step_size: float, input_dict=None, record_outputs=True) -> dict:
        """
        This method updates the input dictionary with the values from the provided input
        dictionary, performs a single step of the simulation on each FMU, using the
        solve_loop method, propagates the output values to the corresponding variables
        for the next step, and updates the current simulation time accordingly. It also
        stores the output values in the results dictionary.

        Args:
            step_size (float): The size of the simulation step.
            input_dict (dict, optional): A dictionary containing input values for the
                simulation. Defaults to None.
            record_outputs (bool, optional): Whether to store the output values in the
                results dictionary. Defaults to True.

        Returns:
            dict: A dictionary containing the output values for this step, structured as
                `[FMU_ID][Var]`.

        """
        self.set_inputs(input_dict=input_dict)

        # Run one step simulation
        self.model.stepUntil(self.current_time + step_size)
        out = self.get_outputs()

        # Save outputs
        if record_outputs:
            self._results["time"].append(self.current_time)
            for fmu_id, outputs in out.items():
                for var_name, value in outputs.items():
                    self._results[(fmu_id, var_name)].extend([value])

        self.current_time += step_size
        return out

        for fmu_ids in self.sequence_order:
            # out is fill with key: fmu_id, value: output_dict (var_name, value)
            out = self.solve_loop(fmu_ids, step_size, algo=self.cosim_method, iterative=self.iterative)

            for fmu_id, fmu_output_dict in out.items():
                for output_name, value in fmu_output_dict.items():
                    # Update inputs connected to FMU outputs
                    self.update_connected_inputs(self._input_dict, fmu_id, output_name, value)
                    if record_outputs:
                        # add each output to the result dict, (FMU_ID + Var) as key
                        self._results[(fmu_id, output_name)].extend(value)

                    # add each output to the output dict, [FMU_ID][Var] as key
                    self._output_dict[fmu_id][output_name] = value

        self.current_time += step_size
        # Return the output value for this step
        return self._output_dict

    def get_residual(self, input_dict: dict, output_dict: dict):
        """
        Performs check between outputs and connected inputs and return a list of
        residuals
        The check is based on connections between given fmu/outputs and inpout dict for
        each FMU.

        Args:
            output_dict: A dictionary containing the output values for the current step
            input_dict: Input dict concerned by the check, transient dict with current
                calculated values

        Returns:
            residuals: A list of residuals between inputs and outputs
                (1 for each connection)
        """
        residuals = {}
        for fmu_id, out_fmu in output_dict.items():
            for output_name, value in out_fmu.items():
                if (fmu_id, output_name) in self.connections:
                    for target_fmu, target_variable in self.connections[(fmu_id, output_name)]:
                        residuals[target_fmu + "_" + target_variable] = np.abs(
                            input_dict[target_fmu][target_variable][0] - value[0]
                        )

        return residuals

    def apply_fmu_outputs_to_inputs(self, input_to_update: dict, fmu_id: str, out_fmu: dict):
        """
        Performs a copy of output values into input dict.
        The copy is based on connections between given fmu/outputs and inpout dict for
        each FMU.

        Args:
            out_fmu: A dictionary containing the output values for the current step
                on a given fmu, identified by fmu_id
            fmu_id: A String identifying FMU into system. Used to find connections with
                outputs
            input_to_update: input dict to update

        Returns:
            No return, at the end of the method, input_to_update is fill with updated
                values.
        """
        for output_name, value in out_fmu.items():
            self.update_connected_inputs(input_to_update, fmu_id, output_name, value)

    def update_connected_inputs(self, input_to_update: dict, fmu_id: str, output_name: str, value):
        """
        Performs a copy of output value into input dict.
        The copy is based on connections between given fmu/output name and inpout dict
        for each connected FMU.

        Args:
            fmu_id: A String identifying FMU into system. Used to find connections
                between inputs and output
            output_name: A string that identifies name of the output. Used to find
                connections with inputs
            value: the value to copy to inputs
            input_to_update: input dict to update

        Returns:
            No return, at the end of the method, input_to_update is fill with updated
                value.
        """
        # If output is connected, transfer the value to the connected FMU(s)
        if (fmu_id, output_name) in self.connections:
            for target_fmu, target_variable in self.connections[(fmu_id, output_name)]:
                if target_fmu in input_to_update:
                    input_to_update[target_fmu][target_variable] = value
