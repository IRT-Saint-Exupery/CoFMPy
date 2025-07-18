# Fixed-Point Initialization in CoFMPy

## Understanding Fixed-Point Initialization

In a co-simulation involving multiple FMUs, the **user-defined initial state** $x_0$ represents the starting values for all system variables. However, if $x_0$ is **not dynamically consistent**, meaning it does not satisfy the physical constraints of the system, the simulation may start from an unrealistic state, leading to numerical instabilities or incorrect results.

To correct this, CoFMPy provides a **fixed-point initialization** process that finds a **valid initial state** $x_0^*$ close to $x_0$, such that:

$$
f(x_0^*) = x_0^*
$$

where $f$ is the **numerical time integrator**, responsible for advancing the system’s state to the next time step (basically built on `do_step`). This ensures that $x_0^*$ is a **fixed-point solution**, meaning the system starts in a physically valid configuration.

## Enabling Fixed-Point Initialization in CoFMPy

To ensure a dynamically valid initialization, you can enable the **fixed-point initialization** by setting `fixed_point_init=True` when starting the simulation coordinator:

```python
coordinator.start(config_path, fixed_point_init=True)
```

When `fixed_point_init=False`, CoFMPy will use the **user-provided** or **default initial values** without verifying their validity. This may be **faster**, but it can lead to **inconsistencies in coupled FMUs**, which may cause instability or incorrect results.

When `fixed_point_init=True`, CoFMPy internally:

1. **Constructs an optimization function** that represents the co-simulation architecture.
2. **Solves for a valid initial state** $x_0^∗$ using a numerical solver, ensuring consistency across all FMUs.
3. **Uses `fsolve` from SciPy** by default to find a solution, using:
    - The **minimum of default integration time steps** defined in each FMU’s XML metadata.
    - Default solver parameters.

### Customizing the Fixed-Point Solver

By default, CoFMPy uses **SciPy's `fsolve`** with its **default arguments**. However, you can customize:

- **The solver method** (`fsolve` or other supported solvers).
- **The fixed-point iteration step size** (`time_step`).
- The solver’s argument passed as keyword arguments dictionnary

To modify these settings, pass the desired options using `fixed_point_kwargs`:



```python
 # Customize fixed point solver
 fixed_point_kwargs = {
      "solver": "fsolve",
      "time_step": 5e-8,
      "tolerance": 1e-5,
      "max_iterations": 100,
  }

  coordinator.start(config_path, fixed_point_init=True, fixed_point_kwargs=fixed_point_kwargs)
```

### Supported Solvers

Currently, CoFMPy supports the following solver:

- **`scipy.optimize.fsolve`**
    - Used for finding roots of nonlinear equations via a **hybrid Powell method**.
    - Automatically approximates the **Jacobian** if not provided.
    - For more details, refer to the SciPy documentation:👉 [fsolve — SciPy v1.15.1 Manual](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fsolve.html)

Support for additional solvers is planned in future versions.
