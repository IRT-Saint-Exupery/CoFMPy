from pythonfmu import Fmi2Causality, Fmi2Variability, Fmi2Slave, Real


class resistor(Fmi2Slave):

    author = "Andrés Lombana"
    description = "Chainable resistor FMU using I_out"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Parameters
        self.R = 1.0

        # Inputs
        self.V_in = 0.0

        # Outputs
        self.I_out = 0.0

        # Register outputs
        self.register_variable(
            Real("I_out", causality=Fmi2Causality.output, variability=Fmi2Variability.continuous)
        )

        # Register parameter
        self.register_variable(
            Real("R", causality=Fmi2Causality.parameter, variability=Fmi2Variability.fixed, start=1.0)
        )

        # Register inputs
        self.register_variable(
            Real("V_in", causality=Fmi2Causality.input, variability=Fmi2Variability.continuous, start=0.0)
        )

    def do_step(self, current_time: float, step_size: float) -> bool:
        # Compute current from voltage input using Ohm's Law
        if self.R != 0:
            self.I_out = self.V_in / self.R
        else:
            # print("set to 0")
            self.I_out = 0.0
        return True
    