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
FMU wrapper classes for FMI 2.0 and FMI 3.0.

This module contains the FMU handler classes for FMI 2.0 and FMI 3.0. These classes are
used to load FMU files and interact with loaded FMUs.
"""

import os
from abc import ABC, abstractmethod

from fmpy import extract, read_model_description
from fmpy.fmi2 import FMU2Slave
from fmpy.fmi3 import FMU3Slave


class FmuHandlerFactory:
    """
    Factory class to create FMU handlers based on the FMI version.

    Attributes:
        path (str): The file path to the FMU.
        description: The model description of the FMU.

    Methods:
        __call__(): Creates and returns an FMU handler based on the FMI version.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, path: str) -> "FmuXHandler":
        """
        Initializes the FmuHandlerFactory with the given path and reads the model
        description.

        Args:
            path (str): The file path to the FMU.

        Returns:
            FmuXHandler: The appropriate FMU handler based on the FMI version.

        Raises:
            ValueError: If the FMI version is not recognized.
        """
        self.path = path
        self.description = read_model_description(path)

    def __call__(self):
        if self.description.fmiVersion == "2.0":
            return Fmu2Handler(self.path, FMU2Slave)
        if self.description.fmiVersion == "3.0":
            return Fmu3Handler(self.path, FMU3Slave)
        raise ValueError("FMI version not recognized")


class FmuXHandler(ABC):
    """
    Abstract base class for handling FMU Slave objects (FMI 2.0 or FMI 3.0).

    Attributes:
        description (ModelDescription): The model description of the FMU.
        var_name2attr (dict): A dictionary mapping variable names to their attributes.
        fmu (FMU): The FMU instance.
        output_var_names (list): A list of output variable names.

    Methods:
        __init__(path: str, fmu_slave):
            Initializes the FMU handler with the given path and FMU slave class.
        reset():
            Abstract method to reset the FMU. Must be implemented by subclasses.
        step(current_time, step_size, input_dict):
            Abstract method to perform a simulation step. Must be implemented by
                subclasses.
        cancel_step():
            Cancels the current step of the FMU.
        get_state():
            Retrieves the current state of the FMU.
        set_state(state):
            Sets the state of the FMU to the given state.
        get_output_names():
            Retrieves the names of the FMU output variables.
        get_input_names():
            Retrieves the names of the FMU input variables.
        get_parameter_names():
            Retrieves the names of the FMU tunable parameters.
    """

    def __init__(self, path: str, fmu_slave):
        """Initializes the FMU handler with the given path and FMU slave class.

        Args:
            path (str): The path of .fmu file to open
            fmu_slave (class): The FMU slave class of FMPy to use to open the fmu
        """
        # read the model description
        self.description = read_model_description(path)

        self.default_step_size = (
            self.description.defaultExperiment.stepSize
            if self.description.defaultExperiment
            else None
        )

        # Create a dictionary to map variable names to attributes
        self.var_name2attr = {}
        for variable in self.description.modelVariables:
            self.var_name2attr[variable.name] = variable

        # extract the FMU and instantiate the slave
        unzipdir = extract(path)
        fmu_name = os.path.basename(path)

        self.fmu = fmu_slave(
            guid=self.description.guid,
            unzipDirectory=unzipdir,
            modelIdentifier=self.description.coSimulation.modelIdentifier,
            instanceName=fmu_name,
        )

        # Get the output variable names
        self.output_var_names = []
        self.output_var_names = list(self.get_output_names())

        # Instantiate the FMU
        self.fmu.instantiate(loggingOn=False)

    def set_variables(self, input_dict: dict):
        """Sets the FMU variables to the given values.

        Args:
            input_dict (dict): A dictionary containing variable names and their
                corresponding values.
        """
        for name, value in input_dict.items():
            self._set_variable(name, value)

    def get_variables(self, names: list[str]) -> dict:
        """Gets the values of the FMU variables matching the given names.

        Args:
            names (list): A list of variable names to get

        Returns:
            dict: A dictionary containing the variable names and their corresponding
                  values
        """
        return {name: self.get_variable(name) for name in names}

    def get_variable_names(self) -> list[str]:
        """Retrieves the names of all variables in the FMU.

        Returns:
            list: A list containing the name of each variable
        """
        return [variable.name for variable in self.description.modelVariables]

    def get_input_names(self) -> list[str]:
        """Retrieves the list of names of the FMU's input variables.

        Returns:
            list: A list containing the name of each input variable
        """
        input_names = []
        for variable in self.description.modelVariables:
            if variable.causality == "input":
                input_names.append(variable.name)
        return input_names

    def get_parameter_names(self) -> list[str]:
        """Retrieves the names of the FMU tunable parameters.
        Returns:
            list: A list containing the name of each tunable parameter
        """
        parameter_names = []
        for variable in self.description.modelVariables:
            if variable.causality == "parameter":
                parameter_names.append(variable.name)
        return parameter_names

    def get_output_names(self) -> list[str]:
        """Retrieves the list of names of the FMU's output variables.

        Returns:
            list: A list containing the name of each output variable
        """
        output_names = []
        for variable in self.description.modelVariables:
            if variable.causality == "output":
                output_names.append(variable.name)
        return output_names

    def get_causality(self, name: str) -> str:
        """Retrieves the causality of a variable.

        Args:
            name (str): The name of the variable to get

        Returns:
            str: The causality of the variable
        """
        return self.var_name2attr[name].causality

    def get_variable_type(self, name: str) -> str:
        """Retrieves the type of the variable with the given name.

        Args:
            name (str): The name of the variable.

        Returns:
            str: The type of the variable.
        """
        return self.var_name2attr[name].type

    def cancel_step(self):
        """Cancels the current step of the FMU."""
        self.fmu.cancelStep()

    def get_state(self):
        """Retrieves the current state of the FMU.

        Returns:
            (fmiXFMUState): The current of state of the FMU, X is the version of FMI used
                (ie. fmi3FMUState for FMI3.0)
        """
        return self.fmu.getFMUstate()

    def set_state(self, state):
        """Sets the state of the FMU to the given state.

        Args:
            state (fmiXFMUState): The state of the FMU to set, X is the version of FMI
                used (ie. fmi3FMUState for FMI3.0)
        """
        self.fmu.setFMUstate(state)

    @abstractmethod
    def _set_variable(self, name, value):
        """Sets the variable matching the given name with the given value."""
        raise NotImplementedError

    def get_variable(self, name: str) -> list:
        """
        Gets the variable matching the given name.

        Args:
            name (str): The name of the variable to get

        Returns:
            list: The value of the variable, as a list.
        """
        var = self.var_name2attr[name]
        return getattr(self.fmu, f"get{var.type}")([var.valueReference])

    @abstractmethod
    def reset(self):
        """Resets the FMU to its initial state and sets up the experiment."""
        raise NotImplementedError

    @abstractmethod
    def step(self, current_time, step_size, input_dict):
        """
        Performs a simulation step with the given current time, step size, and input
        values.
        """
        raise NotImplementedError


class Fmu2Handler(FmuXHandler):
    """
    Handler class for FMU in FMI version 2.0.
    """

    def _set_variable(self, name: str, value: float):
        """
        Sets the variable matching the given name with the given value.

        Args:
            name (str): The name of the input variable to change
            value (float): The desired value to set the variable with
        """
        variable = self.var_name2attr[name]
        self.fmu.setReal([variable.valueReference], value)

    def reset(self):
        """Resets the FMU to its initial state and sets up the experiment."""
        self.fmu.setupExperiment(startTime=0.0)
        self.fmu.enterInitializationMode()
        self.fmu.exitInitializationMode()

    def step(self, current_time: float, step_size: float, input_dict: dict) -> dict:
        """
        Performs a simulation step with the given current time, step size, and input
        values.

        Args:
            current_time (float): the current simulation time.
            step_size (float): the size of the simulation step.
            input_dict (dict): dictionary containing input variable names and their
                corresponding values.

        Returns:
            Dictionary containing output variable names and their corresponding values
                after the simulation step.
        """
        # Set all the input variable that are given
        for name, value in input_dict.items():
            self.fmu.setReal([self.var_name2attr[name].valueReference], value)
            # print(f"{name} : {value}")

        self.fmu.doStep(
            currentCommunicationPoint=current_time, communicationStepSize=step_size
        )
        result = {
            name: self.fmu.getReal([self.var_name2attr[name].valueReference])
            for name in self.get_output_names()
        }
        return result


class Fmu3Handler(FmuXHandler):
    """
    Handler class for FMU in FMI version 3.0.
    """

    def _set_variable(self, name: str, value):
        """
        Sets the variable matching the given name with the given value.

        Args:
            name (str): The name of the input variable to change
            value (float/int/bool/...): The desired value to set the variable with
        """
        variable = self.var_name2attr[name]
        # this is a hack to dynamically call the correct setter function
        # based on the variable type. For example, if the variable type
        # is "Float64", then the setter function is "setFloat64"
        try:
            setter = eval("self.fmu.set" + variable.type)  # pylint: disable=eval-used
            setter([variable.valueReference], value)
        except Exception as e:
            raise ValueError(f"Variable type {variable.type} not supported") from e

    def reset(self):
        """Resets the FMU to its initial state"""
        self.fmu.enterInitializationMode()
        self.fmu.exitInitializationMode()

    def step(self, current_time: float, step_size: float, input_dict: dict) -> dict:
        """
        Performs a simulation step with the given current time, step size, and input
        values.

        Args:
            current_time (float): the current simulation time.
            step_size (float): the size of the simulation step.
            input_dict (dict): dictionary containing input variable names and their
                corresponding values.

        Returns:
            Dictionary containing output variable names and their corresponding values
                after the simulation step.
        """
        # Set all the input variable that are given
        for name, value in input_dict.items():
            if self.var_name2attr[name].type == "Boolean":
                self.fmu.setBoolean([self.var_name2attr[name].valueReference], value)
            else:
                self.fmu.setFloat64([self.var_name2attr[name].valueReference], value)
            # print(f"{name} : {value}")

        self.fmu.doStep(
            currentCommunicationPoint=current_time, communicationStepSize=step_size
        )
        result = {
            name: self.fmu.getFloat64([self.var_name2attr[name].valueReference])
            for name in self.output_var_names
        }
        return result
