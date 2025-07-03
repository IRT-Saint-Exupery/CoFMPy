# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
#    conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
#    of conditions and the following disclaimer in the documentation and/or other
#    materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
import os
import setuptools

# Get the long description from the README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get the version from the VERSION file
with open(os.path.join(this_directory, "cofmpy/VERSION")) as f:
    version = f.read().strip()


def read_requirements(file):
    with open(file, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


dev_requirements = [
    "black",
    "pylint",
    "pytest",
    "pytest-cov",
    "tox",
    "mkdocs",
    "mkdocs-material",
    "mkdocstrings[python]",
    "mkdocs-gallery",
]

setuptools.setup(
    name="cofmpy",
    version="0.0.1",
    author="IRT Saint Exupéry - HECATE project team",
    description="FMUs co-simulation in Python",
    long_description=long_description,
    url="https://github.com/IRT-Saint-Exupery/CoFMPy",
    license="BSD-2-Clause",
    packages=setuptools.find_namespace_packages(),
    include_package_data=True,
    install_requires=read_requirements("requirements.txt"),
    extras_require={"dev": dev_requirements},
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
        "console_scripts": [
            "cofmpy-extract-fmu = cofmpy.helpers.extract_fmu:main",
        ]
    },
)
