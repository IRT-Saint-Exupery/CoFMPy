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

## 🐍 Key Keatures

CoFmuPy provides a Python interface (with a graphical user interface under development) for configuring and running co-simulations of FMI-based systems, with a focus on coordinating interacting FMUs within complex digital twin architectures.

A high-level API allows users to easily define, execute, and visualize digital twins scenarios, while still enabling more advanced control when needed.

Building on the [FMPy library](https://github.com/CATIA-Systems/FMPy) as an FMI-compliant execution backend, CoFmuPy focuses on system-level co-simulation capabilities and advanced coordination logic. In particular, CoFmuPy provides the following key features:

- **Advanced master coordination for coupled FMUs**: Native master algorithms orchestrate the execution of multiple interacting FMUs, ensuring coherent time advancement and stable system-level simulation across heterogeneous subsystems. Cyclic dependencies between FMUs (algebraic loops) are automatically detected and resolved using fixed-point strategies, supporting both Jacobi and Gauss–Seidel co-simulation schemes, with or without rollback. This enables the simulation of tightly coupled systems without manual intervention or model restructuring.

- **Explicit data exchange and synchronization mechanisms**: CoFmuPy provides fine-grained control over data routing, synchronization, and signal propagation between FMUs, as well as between FMUs and external data sources or sinks.

- **Native integration of Python and AI components**: Python-based models (e.g., machine learning or control logic) can be directly integrated into the co-simulation loop without immediate FMU export while still being FMI-compliant, enabling full integration of AI frameworks.

- **Declarative and reproducible configuration**: Co-simulation systems are fully defined through a structured JSON configuration file, making experiments easy to reproduce, modify, and extend.

- **Graphical interface (coming soon)**: A user-friendly graphical interface will enable drag-and-drop system construction, FMU interconnection, remote interfaces configuration, algorithm selection, and co-simulation control.


## 📚 Citation

If you use CoFmuPy in your research or publications, please cite:

```bibtex
@inproceedings{friedrich2025cofmupy,
  title={CoFmuPy: A Python Framework for Rapid Prototyping of FMI-based Digital Twins},
  author={Friedrich, Corentin and Lombana, Andr{\'e}s and Fasquel, J{\'e}r{\^o}me and Schlick, Charlie and Bennani, Nora and Mendil, Mouhcine},
  booktitle={The 2nd International Conference on Engineering Digital Twins},
  year={2025}
}
```


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
