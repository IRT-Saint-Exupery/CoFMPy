"""
Export FMU:
> pythonfmu build -f internal_state_fmu.py --no-external-tool
"""
from pythonfmu import Fmi2Causality
from pythonfmu import Fmi2Slave
from pythonfmu import Fmi2Variability
from pythonfmu import Real


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
