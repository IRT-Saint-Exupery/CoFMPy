# -*- coding: utf-8 -*-
# Copyright 2025 IRT Saint Exupéry and HECATE European project - All rights reserved
#
# The 2-Clause BSD License
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
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import os
import subprocess
import sys
from pathlib import Path


def test_mkdocs_build_no_exception(tmp_path):
    mkdocs_yml = "./mkdocs.yml"
    assert Path(mkdocs_yml).exists(), "mkdocs.yml not found at repo root"

    env = os.environ.copy()
    # To avoid warnings related to UTF-8 encoding
    env["PYTHONUTF8"] = "1"

    # We run `mkdocs build` in a subprocess to ensure no exceptions are raised
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
            "--site-dir",
            str(tmp_path / "site"),
        ],
        cwd=str(Path(".")),
        env=env,
        capture_output=True,
        text=True,
    )

    # Check that the command completed successfully
    assert result.returncode == 0, (
        "mkdocs build failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}\n"
    )
