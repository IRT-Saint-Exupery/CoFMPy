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
import pytest
import json
import os
from cofmpy.config_parser import ConfigParser
from contextlib import contextmanager

@contextmanager
def temp_cwd(path):
    original = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def test_load_config_from_dict():
    config_data = {"fmus": [], "connections": []}
    parser = ConfigParser(config_data)
    assert parser.config_dict == config_data


def test_load_config_from_file(tmp_path):
    config_data = {
        "fmus": [{"id": "FMU1", "initialization": {}, "path": "fmu1.fmu"}],
        "connections": [
            {
                "source": {"id": "A", "variable": "x", "type": "fmu", "unit": ""},
                "target": {"id": "B", "variable": "y", "type": "fmu", "unit": ""},
            }
        ],
        "edge_sep": "test_sep",
        "loop_solver": "test_solver",
        "root": "",
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    parser = ConfigParser(
        str(config_file), loop_solver="test_solver", edge_sep="test_sep"
    )
    assert parser.config_dict == config_data


def test_invalid_file_path():
    with pytest.raises(FileNotFoundError):
        ConfigParser("non_existent.json")


def test_invalid_config_format():
    with pytest.raises(TypeError):
        ConfigParser(123)  # Invalid format


def test_apply_defaults():
    config_data = {"fmus": [], "connections": []}
    parser = ConfigParser(config_data)
    assert parser.config_dict["loop_solver"] == "jacobi"
    assert parser.config_dict["edge_sep"] == " -> "


def test_missing_keys():
    config_data = {"fmus": []}  # Missing "connections"
    parser = ConfigParser(config_data)
    assert parser.config_dict == config_data

    config_data = {"connections": []}  # Missing "fmus"
    with pytest.raises(ValueError):
        ConfigParser(config_data)


def test_build_graph_config():
    config_data = {
        "fmus": [],
        "connections": [
            {
                "source": {"id": "A", "variable": "x", "type": "fmu", "unit": ""},
                "target": {"id": "B", "variable": "y", "type": "fmu", "unit": ""},
            }
        ],
        "edge_sep": " -> ",
    }
    parser = ConfigParser(config_data)
    assert "connections" in parser.graph_config
    assert len(parser.graph_config["connections"]) == 1


def test_update_paths_in_dict(tmp_path):
    config_data = {"fmus": [{"path": "model.fmu"}], "connections": []}
    model_file = tmp_path / "model.fmu"
    model_file.touch()

    parser = ConfigParser(config_data)
    assert parser.config_dict["fmus"][0]["path"] == "model.fmu"


def test_build_master_config():
    config_data = {
        "fmus": [
            {"id": "FMU1", "path": "fmu1.fmu"},
            {"id": "FMU2", "path": "fmu2.fmu"},
        ],
        "connections": [
            {
                "source": {"id": "FMU1", "variable": "x", "type": "fmu", "unit": ""},
                "target": {"id": "FMU2", "variable": "y", "type": "fmu", "unit": ""},
            }
        ],
    }
    parser = ConfigParser(config_data)
    assert "fmus" in parser.master_config
    assert "connections" in parser.master_config
    assert len(parser.master_config["connections"]) == 1
    assert parser.master_config["loop_solver"] == "jacobi"


def test_build_handlers_config():
    config_data = {
        "fmus": [],
        "connections": [
            {
                "source": {
                    "id": "ext_source",
                    "variable": "data",
                    "type": "csv",
                    "unit": "",
                },
                "target": {"id": "FMU1", "variable": "x", "type": "fmu", "unit": ""},
            }
        ],
    }
    parser = ConfigParser(config_data)
    assert len(parser.stream_handlers) == 1
    assert ("FMU1", "x") in parser.stream_handlers


def test_add_symbolic_nodes():
    config_data = {
        "fmus": [],
        "connections": [
            {
                "source": {"type": "csv", "variable": "data"},
                "target": {"id": "FMU1", "variable": "x", "type": "fmu"},
            }
        ],
    }
    parser = ConfigParser(config_data)
    assert len(parser.graph_config["symbolic_nodes"]) == 1


def test_find_corrected_relative_path_found(tmp_path, caplog):
    config_data = {"fmus": [], "connections": []}
    parser = ConfigParser(config_data)

    test_file = tmp_path / "file.txt"
    test_file.touch()

    with temp_cwd(tmp_path):
        with caplog.at_level("INFO"):
            corrected_path = parser._find_corrected_relative_path("file.txt")

    assert corrected_path == "file.txt"
    assert "Success: found file.txt" in caplog.text


def test_find_corrected_relative_path_corrected(tmp_path, caplog):
    config_data = {"fmus": [], "connections": []}
    parser = ConfigParser(config_data)

    # Create file in a subdirectory
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "file.txt").touch()

    # Monkeypatch os.getcwd to base_dir
    with pytest.MonkeyPatch().context() as m:
        m.setattr(os, "getcwd", lambda: str(tmp_path))
        parser.file_path = str(tmp_path / "dummy.json")  # simulate file-based config

        with caplog.at_level("INFO"):
            corrected_path = parser._find_corrected_relative_path("file.txt")

    # Should return a relative path to the found file
    expected_path = os.path.relpath(subdir / "file.txt", tmp_path)
    assert corrected_path == expected_path
    assert f"Info: file.txt replaced by: {expected_path}" in caplog.text


def test_find_corrected_relative_path_not_found(tmp_path, caplog):
    config_data = {"fmus": [], "connections": []}
    parser = ConfigParser(config_data)

    with pytest.MonkeyPatch().context() as m:
        m.setattr(os, "getcwd", lambda: str(tmp_path))
        parser.file_path = str(tmp_path / "some_file.json")

        with caplog.at_level("ERROR"):
            result = parser._find_corrected_relative_path("missing.txt")

    assert result == "missing.txt"
    assert "File not found: missing.txt" in caplog.text
