from cofmpy.utils.proxy import FmuProxy, Variable, FmiCausality


class Resistor(FmuProxy):
    """
    A class representing a resistor component.

    Attributes:
        V (float): The voltage across the resistor in volts.
        I (float): The current flowing through the resistor in amperes.
        R (float): The resistance value of the resistor in ohms.
    """

    # Optional metadata (useful in modelDescription and logs)
    description = "Native Python resistor (FMI-compatible interface)"
    model_identifier = "ResistorProxy"
    default_step_size = 0.01

    def __init__(self, V0: float = 0, R0: float = 1, **kwargs):
        super().__init__(**kwargs)

        # initial values
        self.V = float(V0)  # input
        self.R = float(R0)  # parameter
        self.I = self.V / self.R  # output

        # Register variables (FMI-like descriptors)
        self.register_variable(
            Variable(
                "V",
                causality=FmiCausality.input,
                start=self.V,
            )
        )
        self.register_variable(
            Variable(
                "I",
                causality=FmiCausality.output,
                start=self.I,
            )
        )
        self.register_variable(
            Variable(
                "R",
                causality=FmiCausality.parameter,
                start=self.R,
            )
        )

    def do_step(self, current_time: float, step_size: float) -> bool:
        """Update output current from Ohm's law."""
        self.I = self.V / self.R
        return True
