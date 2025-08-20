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
    name: str
    causality: str
    variability: str = FmiVariability.continuous
    start: Optional[Any] = None
    type: str = "Real"  # "Real" | "Integer" | "Boolean" | "String"


class Real(Variable):
    def __init__(
        self,
        name,
        causality,
        variability=FmiVariability.continuous,
        start: Optional[float] = None,
    ):
        super().__init__(name, causality, variability, start, type="Real")


class Integer(Variable):
    def __init__(
        self,
        name,
        causality,
        variability=FmiVariability.discrete,
        start: Optional[int] = None,
    ):
        super().__init__(name, causality, variability, start, type="Integer")


class Boolean(Variable):
    def __init__(
        self,
        name,
        causality,
        variability=FmiVariability.discrete,
        start: Optional[bool] = None,
    ):
        super().__init__(name, causality, variability, start, type="Boolean")


class String(Variable):
    def __init__(
        self,
        name,
        causality,
        variability=FmiVariability.discrete,
        start: Optional[str] = None,
    ):
        super().__init__(name, causality, variability, start, type="String")


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
    """Python object that mimics an FMI's API."""

    author: str = ""
    description: str = ""
    model_identifier: str = "FmiProxy"
    default_step_size: Optional[float] = None

    def __init__(self):
        self._variables: List[Variable] = []
        # values live as attributes on self (like pythonfmu), but we also
        # keep initial starts to support reset() if user doesn't override it
        self._starts: Dict[str, Any] = {}

    # Registration API (mirrors pythonfmu)
    def register_variable(self, v: Variable):
        self._variables.append(v)
        if v.start is not None and not hasattr(self, v.name):
            setattr(self, v.name, v.start)
        if v.start is not None:
            self._starts[v.name] = v.start

    def variables(self) -> List[Variable]:
        return list(self._variables)

    def reset(self):
        """Default reset: restore declared starts, if any."""
        for v in self._variables:
            if v.name in self._starts:
                setattr(self, v.name, self._starts[v.name])

    # Must be implemented by concrete proxies
    def do_step(self, current_time: float, step_size: float) -> bool:
        raise NotImplementedError


# -------------------------- Utility functions --------------------------


def import_module_from_path(path: str):
    """Import a module from an arbitrary file path (no sys.path pollution)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No such file: {path}")
    module_name = f"_cofmpy_{os.path.splitext(os.path.basename(path))[0]}"
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
        for cls in candidates:
            if cls.__name__ == class_name:
                return cls
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

    # If your code sometimes names the base as ProxyFmu, support both:
    base_cls = FmuProxy
    # Optional: attempt to alias ProxyFmu -> FmuProxy if present in file
    if hasattr(module, "ProxyFmu"):
        proxy_base = getattr(module, "ProxyFmu")
        if inspect.isclass(proxy_base) and issubclass(proxy_base, FmuProxy):
            base_cls = proxy_base  # accept local alias

    return find_proxy_subclass(module, base_cls, class_name=class_name)
