# 🛠️ CoFMPy Helper Scripts

CoFMPy provides a set of **helper scripts** designed to simplify working with
**Functional Mock-up Units (FMUs)** and co-simulation workflows. These scripts offer
**debugging tools, model extraction utilities, and automation features** to enhance user
experience.

---

## 📜 Available Helper Scripts

| Script Name       | Description |
|-------------------|-------------|
| [`cofmpy-extract-fmu`](#extracting-fmu-information-with-cofmpy-extract-fmu) | Extracts and displays all metadata from an FMU file. |
| `User Interface` | 🚧 *Coming soon...* |


## 📦 Extracting FMU Information with `cofmpy-extract-fmu`

The `cofmpy-extract-fmu` helper script is a command-line tool designed to **extract and
display all relevant information** from an FMU (Functional Mock-up Unit) file. It helps
users quickly inspect FMU metadata, including:

- **Inputs, outputs, and parameters**
- **Default values and variable types**
- **Integration step size**

This tool is particularly useful for **debugging, documentation, and ensuring FMU
compatibility** before running co-simulations.

---

### 📜 Usage
The `cofmpy-extract-fmu` script is executed from the command line with the following
syntax:

```sh
cofmpy-extract-fmu <path_to_fmu_file>
```

For example, if you have an FMU file named `model.fmu` in the current directory, run:

```sh
cofmpy-extract-fmu model.fmu
```

This will extract and display all the FMU metadata in a well-structured table.
