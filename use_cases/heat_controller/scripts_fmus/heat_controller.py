"""
Export FMU:
> pythonfmu build -f heat_controller.py --no-external-tool
"""

from pythonfmu import Fmi2Causality, Fmi2Slave, Fmi2Variability, Real


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
