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
Proxy classes module for emulating FMUs with native Python objects.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

import inspect
import importlib.util
import os

# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name

# ---------------- Minimal FMI-like enums (subset) ----------------


class FmiCausality:
    parameter = "parameter"
    input = "input"
    output = "output"
    local = "local"
    independent = "independent"


class FmiVariability:
    constant = "constant"
    fixed = "fixed"
    tunable = "tunable"
    discrete = "discrete"
    continuous = "continuous"


# ---------------- Variable descriptors (inspired by PythonFMU) ----------------


@dataclass
class Variable:
    """
    Represents a variable with associated metadata.

    Attributes:
        name (str): The name of the variable.
        causality (str): The causality of the variable (e.g., input, output, parameter).
        variability (str): The variability of the variable, defaulting to FmiVariability.continuous.
        start (Optional[Any]): The initial value of the variable, if any.
        type (Optional[str]): The data type of the variable, defaulting to "Float16".
    """

    name: str
    causality: str
    variability: str = FmiVariability.continuous
    start: Optional[Any] = None
    type: Optional[str] = "Float16"


# ---------------- Proxy "modelDescription" structs ----------------


@dataclass
class ProxyVarAttr:
    name: str
    type: str
    causality: str
    variability: str
    valueReference: int
    start: Optional[Any] = None


@dataclass
class ProxyCoSimulation:
    modelIdentifier: str = "proxy"
    canGetAndSetFMUstate: bool = True


@dataclass
class ProxyDefaultExperiment:
    stepSize: Optional[float] = None


@dataclass
class ProxyModelDescription:
    fmiVersion: str = "proxy"
    guid: str = "proxy"
    modelVariables: List = field(default_factory=list)
    coSimulation: ProxyCoSimulation = field(default_factory=ProxyCoSimulation)
    defaultExperiment: ProxyDefaultExperiment = field(
        default_factory=ProxyDefaultExperiment
    )


# ---------------- Base class for native Python proxies ----------------


class FmuProxy:
    """
    FmuProxy is a Python class that mimics the API of an FMU.
    It provides a framework for registering and managing variables, as well as
    implementing a simulation step mechanism. This class is intended to be
    subclassed, with the `do_step` method implemented by concrete proxies.
    Attributes:
        author (str): The author of the proxy. Defaults to an empty string.
        description (str): A description of the proxy. Defaults to an empty string.
        model_identifier (str): The identifier for the model. Defaults to "FmuProxy".
        default_step_size (Optional[float]): The default step size for the simulation.
            Defaults to None.
    Methods:
        __init__():
            Initializes the FmuProxy instance, setting up the variables and their initial states.
        register_variable(v: Variable):
            Registers a variable with the proxy. If the variable has a start value, it is added
            as an attribute and stored for reset purposes.
        variables() -> List[Variable]:
            Returns a list of all registered variables.
        reset():
            Restores the initial start values of all registered variables, if they were declared.
        do_step(current_time: float, step_size: float) -> bool:
            Abstract method that must be implemented by subclasses. Represents a simulation step
            and should return a boolean indicating success or failure.
    """

    author: str = ""
    description: str = ""
    model_identifier: str = "FmuProxy"
    default_step_size: Optional[float] = None

    def __init__(self):
        self._variables: List[Variable] = []
        # values live as attributes on self (like pythonfmu), but we also
        # keep initial starts to support reset() if user doesn't override it
        self._starts: Dict[str, Any] = {}

    # Registration API (mirrors pythonfmu)
    def register_variable(self, v: Variable):
        """
        Registers a variable by adding it to the internal list of variables and
        optionally setting its starting value as an attribute of the instance.

        Args:
            v (Variable): The variable to register. It should have a `name` attribute
                          and an optional `start` attribute.

        Behavior:
            - The variable is appended to the internal `_variables` list.
            - If the variable has a `start` value and the instance does not already
              have an attribute with the same name as the variable, the `start` value
              is set as an attribute of the instance.
            - If the variable has a `start` value, it is also stored in the `_starts`
              dictionary with the variable's name as the key.
        """
        self._variables.append(v)
        if v.start is not None and not hasattr(self, v.name):
            setattr(self, v.name, v.start)
        if v.start is not None:
            self._starts[v.name] = v.start

    def variables(self) -> List[Variable]:
        """
        Retrieve the list of variables associated with the fmu proxy.

        Returns:
            List[Variable]: A list containing the variables managed by the fmu proxy.
        """
        return list(self._variables)

    def getFMUstate(self):
        """
        Retrieve the current state of the FMU as a dictionary.

        Returns:
            dict: A dictionary representing the current state of the FMU, with
              variable names as keys and their corresponding values or None.
        """
        """Get the current state of the FMU as a dictionary."""
        state = {}
        for v in self._variables:
            state[v.name] = getattr(self, v.name, None)
        return state

    def setFMUstate(self, state: Dict[str, Any]):
        """
        Set the state of the FMU from a dictionary.

        Args:
            state (Dict[str, Any]): A dictionary where keys are attribute names and
                values are the corresponding values to set.

        Raises:
            AttributeError: If a key in the `state` dictionary does not match any
                existing attribute of the FMU object.
        """
        for name, value in state.items():
            if hasattr(self, name):
                setattr(self, name, value)
            else:
                raise AttributeError(f"Variable '{name}' not found in the FMU.")

    def reset(self):
        """Default reset: restore declared starts, if any."""
        for v in self._variables:
            if v.name in self._starts:
                setattr(self, v.name, self._starts[v.name])

    # Must be implemented by concrete proxies
    def do_step(self, current_time: float, step_size: float) -> bool:
        """
        Performs a single step in the simulation or process.

        This method should be implemented by subclasses to define the behavior
        of a single step given the current time and step size.

        Args:
            current_time (float): The current time in the simulation or process.
            step_size (float): The size of the step to be performed.

        Returns:
            bool: True if the step was successful, False otherwise.

        """
        raise NotImplementedError


# -------------------------- Utility functions --------------------------


def import_module_from_path(path: str):
    """Import a module from an arbitrary file path (no sys.path pollution)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No such file: {path}")
    module_name = f"_cofmupy_{os.path.splitext(os.path.basename(path))[0]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def find_proxy_subclass(
    module, base_cls: Type[FmuProxy], class_name: Optional[str] = None
) -> Type[FmuProxy]:
    """
    Find a subclass of base_cls defined in 'module'.
    - If class_name provided, return that class (validated).
    - Else if exactly one subclass exists, return it.
    - Else raise with a helpful error.
    """
    # Collect candidate classes
    candidates = []
    for _, obj in inspect.getmembers(module, inspect.isclass):
        # Must be defined in this module (avoid pulling from imports)
        if obj.__module__ != module.__name__:
            continue
        if issubclass(obj, base_cls) and obj is not base_cls:
            candidates.append(obj)

    if class_name:
        for candidate_cls in candidates:
            print(f"============ {candidate_cls.__name__} =============")
            if candidate_cls.__name__ == class_name:
                return candidate_cls
        available = ", ".join(c.__name__ for c in candidates) or "<none>"
        raise LookupError(
            f"Class '{class_name}' not found as a subclass of {base_cls.__name__} "
            f"in module {module.__name__}. Available: {available}"
        )

    if len(candidates) == 1:
        return candidates[0]

    if not candidates:
        raise LookupError(
            f"No subclasses of {base_cls.__name__} found in module {module.__name__}."
        )

    names = ", ".join(c.__name__ for c in candidates)
    raise LookupError(
        f"Multiple subclasses of {base_cls.__name__} found in {module.__name__}: {names}. "
        f"Specify which one by adding the <path.py>::<class_name> in config file."
    )


def load_proxy_class_from_file(
    path: str, class_name: Optional[str] = None
) -> Type[FmuProxy]:
    """
    Load and return a subclass of FmuProxy (a.k.a. ProxyFmu) from a .py file.
    If <class_name> is provided, return that class.
    """

    if "::" in path:
        path, class_name = path.split("::", 1)

    module = import_module_from_path(path)

    # If the code sometimes names the base as ProxyFmu, support both:
    base_cls = FmuProxy
    # Optional: attempt to alias ProxyFmu -> FmuProxy if present in file
    if hasattr(module, "ProxyFmu"):
        proxy_base = getattr(module, "ProxyFmu")
        if inspect.isclass(proxy_base) and issubclass(proxy_base, FmuProxy):
            base_cls = proxy_base  # accept local alias

    return find_proxy_subclass(module, base_cls, class_name=class_name)
