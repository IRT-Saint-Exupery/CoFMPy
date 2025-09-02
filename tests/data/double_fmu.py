"""
Export FMU:
> pythonfmu build -f double_fmu.py --no-external-tool
"""
from pythonfmu import Fmi2Causality
from pythonfmu import Fmi2Slave
from pythonfmu import Fmi2Variability
from pythonfmu import Real


class DoubleFMU(Fmi2Slave):
    """
    An FMU that doubles the input: y = 2 * u.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.u: float = 0  # Input
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
        self.y = 2 * self.u
        return True
