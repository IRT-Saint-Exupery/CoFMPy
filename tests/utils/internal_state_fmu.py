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
Export FMU:
> pythonfmu build -f internal_state_fmu.py --no-external-tool
"""

from pythonfmu import Fmi2Causality, Fmi2Slave, Fmi2Variability, Real


class InternalStateFMU(Fmi2Slave):
    """
    An FMU with an internal state, which is used to demonstrate fixed-point
    initialization.

    This FMU has an input `u`, an internal state `x`, and an output `y`. They follow:
    * y = u - x
    * x <- x + 1. x is updated internally (not exposed as an input/output)

    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.u: float = 0  # Input
        self.x: float = 3  # Internal state
        self.y: float = 0  # Output

        self.register_variable(
            Real(
                "u",
                causality=Fmi2Causality.input,
                variability=Fmi2Variability.continuous,
                start=self.u,
            )
        )

        self.register_variable(
            Real(
                "x",
                causality=Fmi2Causality.local,
                variability=Fmi2Variability.continuous,
                initial="exact",
                start=self.x,
            )
        )

        self.register_variable(
            Real(
                "y",
                causality=Fmi2Causality.output,
                variability=Fmi2Variability.continuous,
                initial="exact",
                start=self.y,
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
        self.y = self.u - self.x
        # self.x = self.x + 1
        return True
