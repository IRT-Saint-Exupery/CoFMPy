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
> pythonfmu build -f heat_controller.py --no-external-tool
"""
from pythonfmu import Fmi2Causality
from pythonfmu import Fmi2Slave
from pythonfmu import Fmi2Variability
from pythonfmu import Real


class HeatController(Fmi2Slave):
    """
    A class representing the heat controller for a simulation.

    Attributes:
        amplitude (float): The amplitude of the source in volts.
        frequency (float): The frequency of the source in Hz.
        phase (float): The phase of the source in radians.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.Tc = 18  # Initial temperature setpoint in °C
        self.T_in = 20  # Initial temperature in °C
        self.Kp = 20  # Proportional gain
        self.P_out = 0  # Heating power in W

        self.register_variable(
            Real(
                "Tc",
                causality=Fmi2Causality.input,
                variability=Fmi2Variability.continuous,
            )
        )

        self.register_variable(
            Real(
                "T_in",
                causality=Fmi2Causality.input,
                variability=Fmi2Variability.continuous,
            )
        )

        self.register_variable(
            Real(
                "Kp",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.fixed,
            )
        )

        self.register_variable(
            Real(
                "P_out",
                causality=Fmi2Causality.output,
                variability=Fmi2Variability.continuous,
                initial="exact",
                start=self.P_out,
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
        self.P_out = self.Kp * (self.Tc - self.T_in)
        if self.P_out < 0:
            self.P_out = 0
        elif self.P_out > 100:
            self.P_out = 100
        return True
