<head>
    <meta name="google-site-verification" content="HUjgL1QM39SrK6ApRFAZ1diXfGd99dwkvwsCYaNpi9c" />
</head>

<div align="center">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo_cofmupy_dark.png">
        <source media="(prefers-color-scheme: light)" srcset="docs/assets/logo_cofmupy_light.png">
        <img src="docs/assets/logo_cofmupy_light.png" alt="CoFmuPy logo">
    </picture>
</div>
<br>

<!-- Badge section -->
<div align="center">
    <a href="#">
        <img src="https://img.shields.io/badge/python-3.9%2B-blue"></a>
     <a href="https://github.com/IRT-Saint-Exupery/CoFmuPy/blob/main/LICENSE">
        <img alt="License BSD" src="https://img.shields.io/badge/License-BSD%202--Clause-blue.svg"></a>
    <a href="https://github.com/IRT-Saint-Exupery/CoFmuPy/actions/workflows/python-linters.yml">
        <img alt="Pylint" src="https://github.com/IRT-Saint-Exupery/CoFmuPy/actions/workflows/python-linters.yml/badge.svg"></a>
    <a href="https://github.com/IRT-Saint-Exupery/CoFmuPy/actions/workflows/python-tests.yml">
        <img alt="Tests" src="https://github.com/IRT-Saint-Exupery/CoFmuPy/actions/workflows/python-tests.yml/badge.svg"></a>
    <a href="https://github.com/IRT-Saint-Exupery/CoFmuPy/actions/workflows/python-tests-coverage.yml">
        <img alt="Coverage" src="https://raw.githubusercontent.com/IRT-Saint-Exupery/CoFmuPy/badges/.github/badges/coverage.svg""></a>

</div>
<br>

## 👋 About CoFmuPy

CoFmuPy is a Python library designed for rapid prototyping of digital twins through
the co-simulation of Functional Mock-up Units (FMUs).
It offers advanced master coordination features, such as solving algebraic loops between
FMUs and managing the interaction between various simulation components. This library
provides a seamless interface to orchestrate complex physics simulations and handle the
data exchange between FMUs.

The documentation is available online:
[https://irt-saint-exupery.github.io/CoFmuPy](https://irt-saint-exupery.github.io/CoFmuPy)

## 🐾 Installation

CoFmuPy is available on PyPI and can be installed using `pip`:

```bash
pip install cofmupy
```

## 🐍 Python interface

The Python interface allows users to use CoFmuPy and run co-simulation. A high-level
API is provided to easily run and visualize a co-simulation system.
Advanced users can also dive deeper into the structure of CoFmuPy for a more advanced
control of the components.

Under the hood, CoFmuPy is controlled by a component called the _Coordinator_. It is the
entry point of CoFmuPy and it manages all the other components:

- the Master algorithm which is the engine that runs the co-simulation of FMUs.
- the Graph Engine that builds the connections and interactions between the FMUs and the
  data sources and sinks.
- the data stream handlers that control the input data required by the co-simulation
  system.
- the data storages that allow to store or send the outputs of the simulation.

## 📜 JSON configuration file

To properly define the co-simulation system, a JSON configuration file must be created.
This file is the only information required by CoFmuPy to run the simulation. It must
respect a specific syntax in order to define the FMUs, the interactions between them,
the data sources and sinks, etc.

## ✒️ Contributing

Feel free to propose your ideas or come and contribute with us on the CoFmuPy library!

## 🙏 Acknowledgments

This project was funded by the European Union under GA no 101101961 - HECATE. Views and
opinions expressed are however those of the authors only and do not necessarily reflect
those of the European Union or Clean Aviation Joint Undertaking. Neither the European
Union nor the granting authority can be held responsible for them. The project is
supported by the Clean Aviation Joint Undertaking and its Members.

<div style="display: flex; align-items: center; gap: 20px;">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo_hecate_dark.png" width="48%">
        <source media="(prefers-color-scheme: light)" srcset="docs/assets/logo_hecate_light.png" width="48%">
        <img src="docs/assets/logo_hecate_light.png" alt="HECATE logo">
    </picture>
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo_IRT_dark.png" width="48%">
        <source media="(prefers-color-scheme: light)" srcset="docs/assets/logo_IRT_light.png" width="48%">
        <img src="docs/assets/logo_IRT_light.png" alt="IRT Saint Exupéry logo">
    </picture>
</div>

## 📝 License

The package is released under the [2-Clause BSD License](https://opensource.org/license/bsd-2-clause).
