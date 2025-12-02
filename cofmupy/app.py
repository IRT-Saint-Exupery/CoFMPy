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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Flask Server class
"""
from flask import request
from markupsafe import escape
from flask import Flask

from .config_interface import ConfigObject
from .utils import fmu_utils
from .config_parser import ConfigParser
from .coordinator import Coordinator
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import shutil
import os
import uuid
import json
import pprint

app = Flask("server")
app.secret_key = "super secret key"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
socketio.run(app)

ROOT_PATH_PROJECT = "./projects"


@socketio.on("message")
def handle_message(data):
    print("received message: " + data)
    emit("message", data, broadcast=True)


@app.route("/api/ping")
def hello():
    name = request.args.get("name", "Flask")
    return f"Hello, {escape(name)}!"


@app.route("/api/project/list")
def get_project_list():
    project_list = []
    if not os.path.exists(ROOT_PATH_PROJECT):
        os.mkdir(ROOT_PATH_PROJECT)  # Create root project directory
        return []

    for root, dirs, files in os.walk(ROOT_PATH_PROJECT):
        for dir in dirs:
            with open(
                os.path.join(ROOT_PATH_PROJECT, dir, "metadata.json"),
                "r",
                encoding="utf-8",
            ) as file:
                project = json.load(file)
                with open(
                    os.path.join(ROOT_PATH_PROJECT, dir, "config.json"),
                    "r",
                    encoding="utf-8"
                ) as file_config:
                    project["config"] = json.load(file_config)
                project_list.append(project)

    return project_list


@app.route("/api/project/create", methods=["GET", "POST"])
def create_project():
    project_name = request.form["projectName"]
    project_description = request.form["projectDescription"]
    if os.path.exists(os.path.join(ROOT_PATH_PROJECT, project_name)):
        return {"success": False, "message": "project already exists"}

    os.mkdir(os.path.join(ROOT_PATH_PROJECT, project_name))
    id_project = str(uuid.uuid4())

    project = {
        "id": id_project,
        "name": project_name,
        "description": project_description,
    }
    with open(
        os.path.join(ROOT_PATH_PROJECT, project_name, "metadata.json"),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(project, file, ensure_ascii=False, indent=4)

    with open(
        os.path.join(ROOT_PATH_PROJECT, project_name, "config.json"),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(ConfigObject([], [], []).asdict(), file, ensure_ascii=False, indent=4)

    return project


@app.route("/api/project/delete", methods=["GET", "POST"])
def remove_project():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    shutil.rmtree(project_path)
    # os.removedirs(os.path.join(ROOT_PATH_PROJECT, project_name))

    return {"success": True, "message": "project deleted"}


@app.route("/api/project/load", methods=["GET", "POST"])
def load_project():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.get_config_dict()

    # transform data to interface with frontend
    project["config"] = _transform_config_for_frontend(config, str(project_path))
    return project


@app.route("/api/project/save", methods=["GET", "POST"])
def save_project():
    project = json.loads(request.form["project"])
    project_loaded = _retrieve_project_from_params(project["name"], project["id"])
    project_path = os.path.join(ROOT_PATH_PROJECT, project_loaded["name"])

    # Save metadata file
    with open(
        os.path.join(project_path, "metadata.json"), "w", encoding="utf-8"
    ) as metadata_file:
        json.dump(
            {
                "id": project["id"],
                "name": project["name"],
                "description": project["description"],
            },
            metadata_file,
            ensure_ascii=False,
            indent=4,
        )

    # Save config file
    config = _transform_config_from_frontend(project["config"])
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

    return project


@app.route("/api/project/autoconnection", methods=["GET", "POST"])
def auto_connect_project():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = _transform_config_for_frontend(
        use_case_config.get_config_dict(), project_path
    )
    fmus = config["fmus"]
    new_connections = []
    for indexFmu in range(len(fmus) - 1):
        for inPort in fmus[indexFmu]["inputPorts"]:
            for indexFmu2 in range(indexFmu + 1, len(fmus)):
                outports = [
                    outPort
                    for outPort in fmus[indexFmu2]["outputPorts"]
                    if outPort["name"] == inPort["name"]
                ]
                for outPort2 in outports:
                    new_connections.append(
                        {
                            "source": {
                                "id": fmus[indexFmu2]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": outPort2["name"],
                            },
                            "target": {
                                "id": fmus[indexFmu]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": inPort["name"],
                            },
                        }
                    )
        for outPort in fmus[indexFmu]["outputPorts"]:
            for indexFmu2 in range(indexFmu + 1, len(fmus)):
                inports = [
                    inPort
                    for inPort in fmus[indexFmu2]["inputPorts"]
                    if inPort["name"] == outPort["name"]
                ]
                for inPort2 in inports:
                    new_connections.append(
                        {
                            "source": {
                                "id": fmus[indexFmu]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": outPort["name"],
                            },
                            "target": {
                                "id": fmus[indexFmu2]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": inPort2["name"],
                            },
                        }
                    )
    config["connections"] = new_connections
    config = _transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return config["connections"]


@app.route("/api/fmu/information2", methods=["GET", "POST"])
def get_fmu_information2():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    information = fmu_utils.retrieve_fmu_info(os.path.join(project_path, fmu_info["path"]))
    string_result = "Category;name;start;type\n"
    for information_line in information:
        string_result += (
            str(information_line['category'])
            + ";"
            + str(information_line['name'])
            + ";"
            + str(information_line['start'])
            + ";"
            + str(information_line['type'])
            + "\n"
        )

    return {"success": True, "content": string_result}


@app.route("/api/fmu/information3", methods=["GET", "POST"])
def get_fmu_information3():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    model_description = fmu_utils.get_model_description(
        os.path.join(project_path, fmu_info["path"])
    )

    my_model = {
        "fmiVersion": model_description.fmiVersion,
        "modelName": model_description.modelName,
        "description": model_description.description,
        "author": model_description.author,
        "version": model_description.version,
        "generationDateAndTime": model_description.generationDateAndTime,
        "generationTool": model_description.generationTool,
        "defaultExperiment": (
            {
                "startTime": model_description.defaultExperiment.startTime,
                "stopTime": model_description.defaultExperiment.stopTime,
                "tolerance": model_description.defaultExperiment.tolerance,
                "stepSize": model_description.defaultExperiment.stepSize
            }
            if model_description.defaultExperiment
            else None
        ),
        "coSimulation": {
            "canHandleVariableCommunicationStepSize": model_description.coSimulation.canHandleVariableCommunicationStepSize,
            "fixedInternalStepSize": model_description.coSimulation.fixedInternalStepSize,
            "maxOutputDerivativeOrder": model_description.coSimulation.maxOutputDerivativeOrder,
            "recommendedIntermediateInputSmoothness": model_description.coSimulation.recommendedIntermediateInputSmoothness,
            "canInterpolateInputs": model_description.coSimulation.canInterpolateInputs,
            "providesIntermediateUpdate": model_description.coSimulation.providesIntermediateUpdate,
            "canReturnEarlyAfterIntermediateUpdate": model_description.coSimulation.canReturnEarlyAfterIntermediateUpdate,
            "hasEventMode": model_description.coSimulation.hasEventMode,
            "providesEvaluateDiscreteStates": model_description.coSimulation.providesEvaluateDiscreteStates,
            "canRunAsynchronuously": model_description.coSimulation.canRunAsynchronuously,
            "canGetAndSetFMUstate": model_description.coSimulation.canGetAndSetFMUstate,
            "canSerializeFMUstate": model_description.coSimulation.canSerializeFMUstate
        },
        "modelVariables": [
            {
                "name": modelVariable.name,
                "valueReference": modelVariable.valueReference,
                "type": modelVariable.type,
                "description": modelVariable.description,
                "causality": modelVariable.causality,
                "variability": modelVariable.variability,
                "initial": modelVariable.initial,
                "unit": modelVariable.unit,
                "nominal": modelVariable.nominal,
                "start": modelVariable.start
            }
            for modelVariable in model_description.modelVariables
            if modelVariable.causality != "local"
        ],
    }

    return my_model


@app.route("/api/fmu/delete", methods=["GET", "POST"])
def delete_fmu():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    # Delete fmu file
    os.remove(os.path.join(project_path, fmu_info["path"]))

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.get_config_dict()

    # Delete from fmus list
    fmus = [fmu for fmu in config["fmus"] if fmu["id"] != fmu_info["id"]]
    config["fmus"] = fmus

    # Delete from fmu connections
    connections = [
        connection
        for connection in config["connections"]
        if connection["source"]["id"] != fmu_info["id"]
    ]
    connections = [
        connection
        for connection in connections
        if connection["target"]["id"] != fmu_info["id"]
    ]

    config["connections"] = connections
    config = _transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return project


@app.route("/api/fmu/initialization/edit", methods=["GET", "POST"])
def edit_initialization_fmu():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_id = request.form["fmuId"]
    fmu_name = request.form["fmuName"]
    variable = json.loads(request.form["variable"])
    variable_name = variable["name"]
    variable_value = variable["initialization"]
    variable_type = variable["type"]

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.get_config_dict()

    # Find fmu from fmus list
    fmus = config["fmus"]
    for fmu in config["fmus"]:
        if fmu["id"] == fmu_id and fmu["name"] == fmu_name:
            # Cast String value to correct type : Float, boolean or int
            if variable_type == "Real":
                fmu["initialization"][variable_name] = get_float(variable_value)
            if variable_type == "Integer":
                fmu["initialization"][variable_name] = get_int(variable_value)
            if variable_type == "Boolean":
                fmu["initialization"][variable_name] = get_boolean(variable_value)
            break

    config["fmus"] = fmus
    config = _transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return project


def get_int(value, default=0) -> int:
    try:
        value_return = int(value)
        return value_return
    except ValueError:
        return default


def get_float(value, default=0.0) -> float:
    try:
        value_return = float(value)
        return value_return
    except ValueError:
        return default


def get_boolean(value, default=False) -> bool:
    try:
        value_return = bool(value)
        return value_return
    except ValueError:
        return default


@socketio.on("start_simulation")
def start_simulation(data: any):
    """project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )"""
    project = data["project"]
    communication_time_step = data["communication_time_step"]
    simulation_time = data["simulation_time"]
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    coordinator = Coordinator()
    config_path = os.path.join(project_path, "config.json")
    fsolve_kwargs = {
        "solver": "fsolve",
        "time_step": 1e-5,
        "xtol": 1e-3,
        "maxfev": 10000,
    }
    coordinator.start(
        config_path, fixed_point_init=False, fixed_point_kwargs=fsolve_kwargs
    )

    emit("message", {"message": "Simulation initialized"})

    print("\nConnections are : \n")
    pprint.pp(coordinator.config_parser.master_config["connections"], compact=False)

    coordinator.graph_engine.plot_graph()
    config = coordinator.config_parser.get_config_dict()

    emit("message", {"message": "Simulation start"})
    coordinator.run_simulation(communication_time_step, simulation_time, save_data=True)

    results = coordinator.get_results()
    coordinator.save_results(os.path.join(project_path, "results_simulation.csv"))

    emit(
        "message",
        {
            "message": f"Simulation end with step size {communication_time_step} and time {simulation_time}"
        }
    )


@app.route("/api/simulation/start", methods=["GET", "POST"])
def start_simulation():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    coordinator = Coordinator()
    config_path = os.path.join(project_path, "config.json")
    fsolve_kwargs = {
        "solver": "fsolve",
        "time_step": 1e-5,
        "xtol": 1e-3,
        "maxfev": 10000,
    }
    coordinator.start(
        config_path, fixed_point_init=False, fixed_point_kwargs=fsolve_kwargs
    )

    print("\nConnections are : \n")
    pprint.pp(coordinator.config_parser.master_config["connections"], compact=False)

    coordinator.graph_engine.plot_graph()
    config = coordinator.config_parser.get_config_dict()

    communication_time_step = 0.1
    coordinator.run_simulation(communication_time_step, 30, save_data=True)

    results = coordinator.get_results()
    coordinator.save_results(os.path.join(project_path, "results_simulation.csv"))

    emit("message", {"message": "Simulation ended"}, broadcast=True)

    return {"succes": True}


@app.route("/api/fmu/edit", methods=["GET", "POST"])
def edit_fmu():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmus = json.loads(request.form["fmus"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.get_config_dict()

    config["fmus"] = fmus
    config = _transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return project


@app.route("/api/fmu/upload", methods=["GET", "POST"])
def upload_file():
    project = _retrieve_project_from_params(
        request.form["projectName"], request.form["projectId"]
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    print(request.files)

    with open(
        os.path.join(project_path, "config.json"), "r", encoding="utf-8"
    ) as file_config:
        for file in request.files:

            config = json.load(file_config)
            # parse config to check if fmu already loaded
            fmu_exists = False
            for fmu in config["fmus"]:
                if fmu["path"] == "./" + file:
                    fmu_exists = True
                    break
            if not fmu_exists:
                # save file
                print(f"receive {file}")
                request.files[file].save(os.path.join(project_path, file))

                # Save fmu infos into config
                config["fmus"].append(
                    {
                        "id": fmu_info["id"],
                        "initialization": {},
                        "name": fmu_info["name"],
                        "path": "./" + file,
                    }
                )

    with open(
        os.path.join(project_path, "config.json"), "w", encoding="utf-8"
    ) as file_config_for_write:
        json.dump(config, file_config_for_write, ensure_ascii=False, indent=4)
    return config


def _retrieve_project_from_params(project_name, project_id):
    if not os.path.exists(os.path.join(ROOT_PATH_PROJECT, project_name)):
        raise Exception("Project doesn't exist")

    with open(
        os.path.join(ROOT_PATH_PROJECT, project_name, "metadata.json"),
        "r",
        encoding="utf-8",
    ) as file:
        project = json.load(file)
        # Check project id
        if project["id"] != project_id:
            raise Exception("Bad project id")

    return project


def _transform_config_for_frontend(config: any, project_path: str):
    # Complete fmu sections with fmu details (input and output ports)
    for fmu in config["fmus"]:
        table_result = fmu_utils.retrieve_fmu_info(os.path.join(project_path, fmu["path"]))
        input_ports = []
        output_ports = []
        if table_result is not None:
            for line in table_result:
                excluded = False
                """for exclude_pattern in exclude_ports_patterns:
                    if line["name"].find(exclude_pattern) != -1:
                        excluded = True"""
                if not excluded:
                    if line["category"] == "Input":
                        input_ports.append(line)
                    if line["category"] == "Output":
                        output_ports.append(line)
        fmu["inputPorts"] = input_ports
        fmu["outputPorts"] = output_ports
    return config


def _transform_config_from_frontend(config: any):
    # Refactor connections
    #     target as an array
    factorized_connections = []
    for connection in config["connections"]:
        # Look for existing item with same source
        found_source = False
        for fact_connection in factorized_connections:
            fact_source = fact_connection["source"]
            if (
                fact_source["id"] == connection["source"]["id"]
                and fact_source["variable"] == connection["source"]["variable"]
            ):
                fact_connection["target"].extend([connection["target"]])
                found_source = True
        if not found_source:
            factorized_connections.append(
                {"source": connection["source"], "target": [connection["target"]]}
            )
    config["connections"] = factorized_connections

    # Refactor fmu to remove inputPorts and outputPorts
    for fmu in config["fmus"]:
        if "inputPorts" in fmu:
            del fmu["inputPorts"]
        if "outputPorts" in fmu:
            del fmu["outputPorts"]
        if "info" in fmu:
            del fmu["info"]

    # Refactor data_storages before save : remove config.items and config.labels
    for storage in config["data_storages"]:
        del storage["config"]["items"]
        del storage["config"]["labels"]

    return config
