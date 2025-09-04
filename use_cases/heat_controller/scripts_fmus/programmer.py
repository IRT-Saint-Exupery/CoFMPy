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
Export FMU:
> pythonfmu build -f programmer.py --no-external-tool
"""
from pythonfmu import Fmi2Causality
from pythonfmu import Fmi2Slave
from pythonfmu import Fmi2Variability
from pythonfmu import Real


class Programmer(Fmi2Slave):
    """
    A class representing a programmer for a heater. It permits a more complex
        simulation heater and heater controller fmu

    This fmu has 2 possible range of programming, which can be set thanks to 6
        available parameters :
        - t1_start : time for start range 1
        - t1_stop : time for stop range 1
        - t1_temp : consign temperature for range 1
        - t2_start : time for start range 2
        - t2_stop : time for stop range 2
        - t2_temp : consign temperature for range 2

    There is 1 output for this fmu, named T_out : the desire temperature pending
        parameters and current time. Default external temp is 17

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.default_temp = 17

        self.t1_start = 0
        self.t1_stop = 0
        self.t1_temp = 0
        self.t2_start = 0
        self.t2_stop = 0
        self.t2_temp = 0
        self.T_out = self.default_temp

        self.register_variable(
            Real(
                "t1_start",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "t1_stop",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "t1_temp",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "t2_start",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "t2_stop",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "t2_temp",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
                initial="exact",
                start=0,
            )
        )
        self.register_variable(
            Real(
                "T_out",
                causality=Fmi2Causality.output,
                variability=Fmi2Variability.continuous,
                initial="exact",
                start=self.default_temp,
            )
        )

    def do_step(self, current_time, step_size):
        """
        Perform a simulation step.

        Args:
            current_time (float): The current simulation time.
            step_size (float): The size of the simulation step.

        Returns:
            bool: True if the step was successful, False otherwise.
        """
        if self.t1_start != self.t1_stop \
                and self.t1_start < current_time < self.t1_stop:
            self.T_out = self.t1_temp
        elif self.t2_start != self.t2_stop \
                and self.t2_start < current_time < self.t2_stop:
            self.T_out = self.t2_temp
        else:
            self.T_out = self.default_temp

        return True
