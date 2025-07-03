"""
Export FMU:
> pythonfmu build -f heater.py --no-external-tool
"""

from pythonfmu import Fmi2Causality, Fmi2Slave, Fmi2Variability, Real


class Heater(Fmi2Slave):
    """
    A class representing a heater for a simulation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.T_out = 20  # Initial temperature in °C
        self.P_in = 0  # Heating power in W
        self.heat_loss = 0.1  # Heat loss per second in °C

        self.register_variable(
            Real(
                "T_out",
                causality=Fmi2Causality.output,
                variability=Fmi2Variability.continuous,
                initial="exact",
                start=self.T_out,
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
                "heat_loss",
                causality=Fmi2Causality.parameter,
                variability=Fmi2Variability.tunable,
                start=self.heat_loss,
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
        self.T_out += step_size * (self.P_in / 100 - self.heat_loss)
        return True
