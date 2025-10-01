"""
Export FMU:
> pythonfmu build -f math_fmu.py --no-external-tool
"""
from pythonfmu3 import Fmi3Causality
from pythonfmu3 import Fmi3Slave
from pythonfmu3 import Fmi3Variability
from pythonfmu3 import Float64


class MathFMUV3(Fmi3Slave):
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
        self.time = 0

        self.register_variable(
            Float64(
                "p",
                causality=Fmi3Causality.parameter,
                variability=Fmi3Variability.tunable,
                start=self.p,
            )
        )

        self.register_variable(
            Float64(
                "u",
                causality=Fmi3Causality.input,
                variability=Fmi3Variability.continuous,
                start=self.u,
            )
        )

        self.register_variable(
            Float64(
                "x",
                causality=Fmi3Causality.input,
                variability=Fmi3Variability.continuous,
            )
        )

        self.register_variable(
            Float64(
                "y",
                causality=Fmi3Causality.output,
                variability=Fmi3Variability.continuous,
                initial="exact",
                start=self.y,
            )
        )
        self.register_variable(
            Float64(
                "time",
                causality=Fmi3Causality.independent,
                variability=Fmi3Variability.continuous

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
        self.time = current_time
        self.y = 0.8 * self.x + (1 + self.u)
        return True
