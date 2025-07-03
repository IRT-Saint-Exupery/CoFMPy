# Use case "Heat Controller"

This use case represents a heater regulated by a proportional controller. The system is
split into two subsystems simulated with two FMUs generated from Python code:

- `Heater.fmu`: an FMU that takes as inputs the previous temperature and the heat
  command, and returns the new temperature. The new temperature follows
  `T_out = T_in + dt * (P_in/100 - heat_loss)`.
- `HeatController.fmu`: an FMU that takes as input the temperature and the setpoint
  temperature `Tc` and returns the heat command to give to the heater.

## Inputs and outputs

- Heater:
  - input: `P_in` (the heat power of the heater)
  - outputs: `T_out` (the temperature of the heater)
- HeatController:
  - inputs: `T_in` and `Tc` (the temperature of the heater and the setpoint temperature)
  - output: `P_out` (the power to apply to the heater)

The FMUs are connected with 2 connections:

- Heater.T_out -> HeatController.T_in
- HeatController.P_out -> Heater.P_in

## Generate the FMUs

The FMUs are not directly provided but two Python scripts are given. You can generate
the FMUs using `pythonfmu`.

Run the Python script `generate_fmus.py` (make sure `pythonfmu` is installed):

```bash

python generate_fmus.py
```

You can find details about the behaviour of the FMUs in the Python scripts `heater.py`
and `heat_controller.py`.

## Run notebook

The `config.json` file contains the configuration for the CoFMPy simulation. You can
execute the main notebook to run the co-simulation.
