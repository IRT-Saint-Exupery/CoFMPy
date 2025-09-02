"""
Export FMU:
> pythonfmu build -f math_fmu.py --no-external-tool
"""
from pythonfmu import Fmi2Causality
from pythonfmu import Fmi2Slave
from pythonfmu import Fmi2Variability
from pythonfmu import Real


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
