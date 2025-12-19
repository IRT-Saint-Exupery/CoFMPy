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
"""
Unit tests for the Server object.

The tests are based on the following use cases:
    1. Single FMU bouncing ball.
    2. Two FMUs with a single connection (source -> resistor).

"""
import json
from collections import defaultdict

import numpy as np
import pytest

from cofmupy.server.app import app

use_cases = [
    {  # Use case 1: single FMU bouncing ball
        "use_case_name": "bouncing_ball",
        "description": "Hello I'm a bouncing ball, catch me if you can !!",
        "expected_projects": 1,
        "expected_connection_number": 0,
        "fmus": [
            {
                "id": "ball",
                "name": "BouncingBall",
                "path": "resources/fmus/BouncingBall.fmu",
                "initialization": {"e": 0.6},  # coefficient of restitution
            }
        ],
    },
    {  # Use case 2: two FMUs with a single connection (source -> resistor)
        # jacobi algo
        "use_case_name": "source_resistor",
        "description": "Standard Source/Resistor with Voltage connection",
        "expected_projects": 2,
        "expected_connection_number": 1,
        "fmus": [
            {
                "id": "source",
                "name": "source",
                "path": "resources/fmus/source.fmu",
                "initialization": {"phase": 0.9},
            },
            {
                "id": "resistor",
                "name": "resistor",
                "path": "resources/fmus/resistor.fmu",
                "initialization": {"R": 5.0},
            }
        ],
    },
]
@pytest.fixture(
    params=use_cases,
    ids=lambda param: param["use_case_name"],
)
def use_case(request):
    return request.param

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_ping(client, use_case):
    response = client.get(f"/api/ping?name={use_case['use_case_name']}")
    assert response.status_code == 200
    assert response.text == f"Hello, {use_case['use_case_name']}!"


def test_project_create(client, use_case):
    # Check project list is empty
    response = client.get("/api/project/list")
    assert response.status_code == 200
    assert len(response.json) == use_case["expected_projects"]-1

    # Create project
    args = {
        "projectName": use_case["use_case_name"],
        "projectDescription": use_case["description"],
    }
    response_create = client.post("/api/project/create", data=args)
    assert response_create.status_code == 200
    project_id = response_create.json['id']

    # Check project list is not empty
    response = client.get("/api/project/list")
    assert response.status_code == 200
    assert len(response.json) == use_case["expected_projects"]
    found_project = False
    for project in response.json:
        if project["name"] == use_case["use_case_name"]:
            found_project = True
            assert project["description"] == use_case["description"]
    assert found_project


def retrieve_project_by_name(client, name: str):
    response = client.get("/api/project/list")
    for project in response.json:
        if project["name"] == name:
            return project
    return None


def test_load_project(client, use_case):
    project = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None
    args = {
        "projectName": project["name"],
        "projectId": project["id"],
    }
    response = client.post("/api/project/load", data=args)
    assert response.status_code == 200
    assert response.json["name"] == use_case["use_case_name"]
    print(f"\n{response.json}")


def test_save_project(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None
    assert "config" in project.keys()
    project["config"]["cosim_method"] = "gauss_seidel"

    args = {
        "project": json.dumps(project),
    }
    response = client.post("/api/project/save", data=args)
    assert response.status_code == 200
    assert response.json["config"]["cosim_method"] == "gauss_seidel"


def test_upload_fmu(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    for fmu in use_case["fmus"]:
        file_name = f"{fmu['name']}.fmu"
        data = {
            file_name: (open(fmu["path"], "rb"), fmu["name"]),
            "projectName": project["name"],
            "projectId": project["id"],
            "fmu": json.dumps(fmu),
        }
        response = client.post(
            "/api/fmu/upload", data=data, content_type='multipart/form-data'
        )
        assert response.status_code == 200
    assert len(response.json["fmus"]) == len(use_case["fmus"])


def test_auto_connect(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    args = {
        "projectName": project["name"],
        "projectId": project["id"],
    }
    response = client.post("/api/project/autoconnection", data=args)
    assert response.status_code == 200
    assert len(response.json) == use_case["expected_connection_number"]


def test_fmu_information(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    for fmu in project["config"]["fmus"]:
        args = {
            "projectName": project["name"],
            "projectId": project["id"],
            "fmu": json.dumps(fmu),
        }
        response = client.post("/api/fmu/information2", data=args)
        assert response.status_code == 200
        assert len(response.json["content"]) > 0


def test_fmu_information_2(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    for fmu in project["config"]["fmus"]:
        args = {
            "projectName": project["name"],
            "projectId": project["id"],
            "fmu": json.dumps(fmu),
        }
        response = client.post("/api/fmu/information3", data=args)
        assert response.status_code == 200
        assert "coSimulation" in response.json.keys()
        assert "modelVariables" in response.json.keys()
        assert len(response.json["modelVariables"]) > 0


def test_fmu_initialization(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    for fmu in use_case["fmus"]:
        for variable, value in fmu["initialization"].items():
            args = {
                "projectName": project["name"],
                "projectId": project["id"],
                "fmuId": fmu["id"],
                "fmuName": fmu["name"],
                "variable": json.dumps(
                    {"name": variable, "initialization": value, "type": "Real"}
                )
            }
            response = client.post("/api/fmu/initialization/edit", data=args)
            assert response.status_code == 200


def test_fmu_delete(client, use_case):
    project: dict = retrieve_project_by_name(client, use_case["use_case_name"])
    assert project is not None

    for fmu in project["config"]["fmus"]:
        args = {
            "projectName": project["name"],
            "projectId": project["id"],
            "fmu": json.dumps(fmu),
        }
        response = client.post("/api/fmu/delete", data=args)
        assert response.status_code == 200
    assert len(response.json["fmus"]) == 0
    assert len(response.json["connections"]) == 0

def test_project_delete(client):
    # Check project list is not empty
    response = client.get("/api/project/list")
    assert response.status_code == 200
    assert len(response.json) == len(use_cases)

    for project in response.json:
        # Delete project
        args_delete = {
            "projectName": project["name"],
            "projectId": project["id"],
        }
        response_delete = client.post("/api/project/delete", data=args_delete)
        assert response_delete.status_code == 200

    # Check project list is empty
    response = client.get("/api/project/list")
    assert response.status_code == 200
    assert len(response.json) == 0

"""
TODO : unit test on start simulation, and on socket protocol
"start_simulation"
"message"
"""
