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
Export FMU:
> pythonfmu build -f heater_thermal_model.py --no-external-tool
"""
from pythonfmu import Fmi2Causality, Fmi2Slave, Fmi2Variability, Real


class HeaterThermalModel(Fmi2Slave):
    """
    A class representing a heater for a simulation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.T_in: float = 0  # Initial temperature in °C (input)
        self.P_in: float = 0  # Heating power in W (input)
        self.nominal_heat_loss: float = 0.1  # The nominal heat loss per second in °C
        self.T_out: float  # Temperature in °C estimated at next time step (output)

        self.register_variable(
            Real(
                "T_out",
                causality=Fmi2Causality.output,
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
                "P_in",
                causality=Fmi2Causality.input,
                variability=Fmi2Variability.continuous,
            )
        )

        self.register_variable(
            Real(
                "nominal_heat_loss",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.tunable,
                start=self.nominal_heat_loss,
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
        self.T_out = self.T_in + step_size * (self.P_in / 100 - self.nominal_heat_loss)
        return True
