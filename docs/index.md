<div align="center">
    <img src="./assets/logo_cofmpy_dark.png#only-dark" width="75%" alt="Logo CoFMPy" align="center" />
    <img src="./assets/logo_cofmpy_light.png#only-light" width="75%" alt="Logo CoFMPy" align="center" />
</div>
<br>

## 👋 About CoFMPy

CoFMPy is a Python library designed for co-simulating Functional Mock-up Units (FMUs).
It offers advanced master coordination features, such as solving algebraic loops between
FMUs and managing the interaction between various simulation components. This library
provides a seamless interface to orchestrate complex physics simulations and handle the
data exchange between FMUs.

The documentation is available online: https://irt-saint-exupery.github.io/CoFMPy/


## 🐾 Installation

CoFMPy is available on PyPI and can be installed using `pip`:

```bash
pip install cofmpy
```

<!--
## 🖥️ Graphical Interface

The web interface allows users to interact with the cosimulation through a user-friendly
graphical interface.

You can start the web application by running the following command:

```shell
streamlit run cofmpy/webapp/main.py
```

Once the web application is running, you can access it by opening your web browser and
navigating to the provided URL. From there, you can explore the various features and
functionalities of CoFMPy's web interface.

This web interface is still under development, and additional features and improvements
will be added in the future.
-->

## 🐍 Python interface

The Python interface allows users to use CoFMPy and run co-simulation. A high-level
API is provided to easily run and visualize a co-simulation system.
Advanced users can also dive deeper into the structure of CoFMPy for a more advanced
control of the components.

Under the hood, CoFMPy is controlled by a component called the _Coordinator_. It is the
entry point of CoFMPy and it manages all the other components:

- the Master algorithm which is the engine that runs the co-simulation of FMUs.
- the Graph Engine that builds the connections and interactions between the FMUs and the
  data sources and sinks.
- the data stream handlers that control the input data required by the co-simulation
  system.
- the data storages that allow to store or send the outputs of the simulation.
- the GUI as the frontend of CoFMPy.

## 📜 JSON configuration file

To properly define the co-simulation system, a JSON configuration file must be created.
This file is the only information required by CoFMPy to run the simulation. It must
respect a specific syntax in order to define the FMUs, the interactions between them,
the data sources and sinks, etc.

## ✒️ Contributing

Feel free to propose your ideas or come and contribute with us on the CoFMPy library!

## 🙏 Acknowledgments

This project was funded by the European Union under GA no 101101961 - HECATE. Views and
opinions expressed are however those of the authors only and do not necessarily reflect
those of the European Union or Clean Aviation Joint Undertaking. Neither the European
Union nor the granting authority can be held responsible for them. The project is
supported by the Clean Aviation Joint Undertaking and its Members.

<div style="display: flex; align-items: center; gap: 20px;">
    <img src="./assets/logo_hecate_dark.png#only-dark" width="48%" alt="Logo HECATE" />
    <img src="./assets/logo_hecate_light.png#only-light" width="48%" alt="Logo HECATE" />
    <img src="./assets/logo_IRT_dark.png#only-dark" width="48%" alt="Logo IRT Saint Exupéry" />
    <img src="./assets/logo_IRT_light.png#only-light" width="48%" alt="Logo IRT Saint Exupéry" />
</div>

## 📝 License

The package is released under the [2-Clause BSD License](https://opensource.org/license/bsd-2-clause).
