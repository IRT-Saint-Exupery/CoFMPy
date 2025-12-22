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
This module contains the base class for the master algorithms.
"""
from abc import abstractmethod
from typing import Any


class BaseMaster:
    """
    Base class for Master algorithm that runs the co-simulation and handles the
    algebraic loops.

    Child classes must implement the abstract methods defined in this class:
        - variable_names: property returning the list of variable names in the system.
        - get_variable: get the value of a variable.
        - get_causality: get the causality of a variable (e.g., input, output).
        - get_variable_type: get the type of a variable (e.g., Real, Integer).
        - get_outputs: get the outputs at the current step.
        - get_results: get the results of the simulation up to the current time.
        - init_simulation: initialize the simulation environment.
        - do_step: perform a simulation step.
    """

    # Type name of the master subclass (used in the configuration file)
    type_name = None

    # Registry of available master classes
    _masters_registry = {}

    @abstractmethod
    def __init__(self):
        pass

    @classmethod
    def register_master(cls, subclass):
        """Register a subclass master in the registry.

        The subclass must inherit from BaseMaster and have a `type_name` class
        attribute. The `type_name` attribute is used to identify the master type in the
        configuration file.

        Args:
            subclass (BaseMaster): master subclass to register.
        """
        if not issubclass(subclass, BaseMaster):
            raise TypeError(f"Class {subclass.__name__} must inherit from BaseMaster.")
        key = subclass.type_name
        cls._masters_registry[key] = subclass

    @classmethod
    def create_master(cls, config_dict):
        """Factory method to create a class instance based on config_dict.

        The config_dict must contain a `type` key that corresponds to the `type_name`
        class attribute of the master subclass. The config_dict also contains a config
        dictionary that is passed to the master constructor.

        Args:
            config_dict (dict): configuration dictionary. Must contain a `type` key and
                a `config` key to initialize the master.

        Returns:
            BaseMaster: a new master instance.
        """
        master_type = config_dict.get("type")
        if master_type not in cls._masters_registry:
            raise ValueError(
                f"Unknown master type '{master_type}'."
                f"Available types: {list(cls._masters_registry.keys())}"
            )
        return cls._masters_registry[master_type](**config_dict["config"])

    @property
    @abstractmethod
    def variable_names(self) -> list[tuple[str, str]]:
        """
        Get the names of all variables in the system.

        Returns:
            list: list of variable names as (fmu_id, var_name) tuples.
        """

    @abstractmethod
    def get_variable(self, name: tuple[str, str]):
        """
        Get the value of the given tuple fmu/variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            list: value of the variable, as a list.
        """

    @abstractmethod
    def get_causality(self, name: tuple[str, str]) -> str:
        """
        Gets the causality of the given variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            str: causality of the variable.
        """

    @abstractmethod
    def get_variable_type(self, name: tuple[str, str]) -> str:
        """
        Get the type of the given variable.

        Args:
            name (tuple): variable name as (fmu_id, var_name).

        Returns:
            str: type of the variable.
        """

    @abstractmethod
    def get_outputs(self) -> dict[str, dict[str, Any]]:
        """
        Returns the output dictionary for the current step.

        Returns:
            dict: A dictionary containing the output values of the current step,
                structured as `[FMU_ID][Var]`.
        """

    @abstractmethod
    def get_results(self) -> dict:
        """
        Returns the results of the simulation, this includes the values of every output
        variables, for each step, up until the current time of simulation.

        Returns:
            dict: A dictionnary containing output values of every step, structured as
                [(FMU_ID, Var)]

        """

    @abstractmethod
    def init_simulation(self, input_dict: dict[str, dict[str, Any]] = None):
        """
        Initializes the simulation environment, FMUs and variables.

        Args:
            input_dict (dict, optional): Dictionary of input values to set at
                initialization. Defaults to None.
        """

    @abstractmethod
    def do_step(self, step_size: float, input_dict=None, record_outputs=True) -> dict:
        """
        This method performs a single step of the system co-simulation. Input variables
        are updated before simulation if an `input_dict` is given. Output variables are
        retrieved after the step and returned as a dictionary. If `record_outputs` is
        set to True, the output values are also stored in the global results dictionary.

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
