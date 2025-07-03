# ✒️ Contributing to CoFMPy

First off, thank you for considering contributing to **CoFMPy**! By contributing, you
help improve this project and make it available to many others. We welcome contributions
in various forms, whether it’s through code, documentation, bug reports, or feature
suggestions.

## How to Contribute

We appreciate all kinds of contributions. Whether you find bugs, want to improve
documentation, or implement new features, there are several ways you can contribute.

### Reporting Issues

If you find a bug or unexpected behavior, please follow these steps:
1. **Search** the existing issues to check if it has already been reported.
2. If it's a new issue, create a **new issue** with the following information:
   - A clear description of the problem.
   - Steps to reproduce the issue (if possible).
   - Your environment details (e.g., operating system, Python version).
   - Error messages or logs, if any.

### Suggesting Enhancements

We love hearing about new ideas for features or improvements! To suggest a feature:
1. **Search** to see if someone else has already suggested it.
2. If it's not already suggested, create a **new issue** to describe the enhancement:
   - A clear explanation of the feature and its use cases.
   - Why it would be valuable to the project.
   - If applicable, any examples of how the feature might work.

### Submitting Code

We welcome code contributions! If you want to submit code, please follow the steps
below.

1. **Fork the repository** and clone your fork to your local machine.
2. **Create a new branch** for your changes. Try to name it meaningfully, such as
   `fix/bug-description` or `feature/feature-name`.
3. **Make your changes**. Ensure that your changes don't break the existing
   functionality. Follow Pylint style guidelines.
4. **Write tests** to cover your changes, if applicable. See the [Testing](#testing)
   section for more details.
5. **Commit your changes** with a descriptive commit message.
6. **Push your branch** to your fork on GitHub.
7. **Open a Pull Request (PR)** with a clear description of your changes.

## Setup Installation for Developers

To get started with contributing to this project, you'll need to set up your development
environment.

1. Clone the repo: `git clone https://github.com/blabla/cofmpy.git`
2. Go to the root of the repo: `cd cofmpy`
3. Create a new virtual environement:
    - using `venv` on Linux:

      ```bash
      python3 -m venv env_cofmpy
      source env_cofmpy/bin/activate
      ```

    - using `venv` on Windows:

      ```powershell
      python3 -m venv env_cofmpy
      env_cofmpy/Scripts/activate.bat
      ```

    - using `conda`:

      ```bash
      conda create -n env_cofmpy python=3.10
      conda activate env_cofmpy
      ```

4. Install dependencies using `pip`:

   ```bash
   pip install -U pip
   pip install -r requirements.txt -r requirements_dev.txt
   pip install -e .
   ```

Your environment is now ready for development! You can run `pytest` to verify that the
environment is set up correctly.

## Coding Guidelines

- **Write clear, concise code** that follows Python best practices.
- Ensure that your code is **compatible with Python 3.9+**.
- **Document your code** with docstrings, especially for functions, classes, and
  modules.

## Testing

- Write tests for your changes (if applicable). We use [pytest](https://pytest.org/) for
  testing, so please ensure your code passes the existing tests as well as any new ones.
- To run CI tests locally, use either:
  - `tox` environments, e.g. `tox -e py310-lint` for format/lint checks and `tox -e
    py310` for pytest unit tests.
  - or directly using `black`, `pylint` and `pytest`:

  ```bash
  python -m black --check --diff
  python -m pylint cofmpy
  pytest
  ```

## Generating Documentation

The documentation is generated with MkDocs. From the root of the repo, you can generate
the documentation and run the live server with:

```bash
mkdocs serve
```
