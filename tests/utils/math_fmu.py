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
> pythonfmu build -f math_fmu.py --no-external-tool
"""

from pythonfmu import Fmi2Causality, Fmi2Slave, Fmi2Variability, Real


class MathFMU(Fmi2Slave):
    """
    An FMU that performs a simple mathematical operation:
    y = 0.8 * x + (1 + u).

    x and u are inputs, and y is the output. p is a tunable parameter but unused.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.p: float = 0  # Parameter
        self.u: float = 0  # Input
        self.x: float = 0  # Input
        self.y: float = 0  # Output

        self.register_variable(
            Real(
                "p",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.tunable,
                start=self.p,
            )
        )

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
                causality=Fmi2Causality.input,
                variability=Fmi2Variability.continuous,
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
        self.y = 0.8 * self.x + (1 + self.u)
        return True
