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
from markupsafe import escape
from flask import request
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from ..config_interface import ConfigObject
from ..utils import fmu_utils
from ..utils import types
from ..config_parser import ConfigParser
from ..coordinator import Coordinator
from .services import transform_config_from_frontend
from .services import transform_config_for_frontend
from .services import retrieve_project_from_params
import shutil
import os
import uuid
import json
import pprint

app = Flask(__name__)
app.secret_key = "CoFmuPy secret key"

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all requesters

ROOT_PATH_PROJECT = "./projects"


@socketio.on("message")
def handle_message(data: str):
    """
    Manage socket message sent from external tool (Hmi)

    Args:
        data (str): Message from external tool. Bidirectional communication is working,
            it should be improved with more consistent messages and according actions
    """
    print("received message: " + data)
    emit("message", data, broadcast=True)


@app.route("/api/ping")
def hello():
    """
    Route for test purpose. Navigate or request to url http://localhost:5000/api/ping
        to check application is alive
    """
    name = request.args.get("name", "Flask")
    return f"Hello, {escape(name)}!"


@app.route("/api/project/list")
def get_project_list():
    """
    Retrieve project list managed by the server, for each sub-directories, parse
        metadata and append config information to construct response.
    Root project path is defined into global variable ROOT_PATH_PROJECT.

    Returns:
        list: List of dict containing projects information.
    """
    project_list = []
    if not os.path.exists(ROOT_PATH_PROJECT):
        os.mkdir(ROOT_PATH_PROJECT)  # Create root project directory
        return []

    # pylint: disable=W0612
    for root, dirs, files in os.walk(ROOT_PATH_PROJECT):
        for directory in dirs:
            with open(
                os.path.join(ROOT_PATH_PROJECT, directory, "metadata.json"),
                "r",
                encoding="utf-8",
            ) as file:
                project = json.load(file)
                with open(
                    os.path.join(ROOT_PATH_PROJECT, directory, "config.json"),
                    "r",
                    encoding="utf-8",
                ) as file_config:
                    project["config"] = json.load(file_config)
                project_list.append(project)

    return project_list


@app.route("/api/project/create", methods=["GET", "POST"])
def create_project():
    """
    End-point to create project, this method makes sub-directory into root project path,
        create metadata.json with inputs parameters and create empty config.json file.

    Args (included into form's request) :
        projectName (str): project name to create.
        projectDescription (str): project description to create.
    Returns:
        dict:
            - On success : return created project.
            - On project exists : return response including error message
    """
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
    """
    End-point to delete project, this method deletes all project directory with
        all contained files.

    Args (included into form's request) :
        projectName (str): project name eto delet, corresponding to sub-directory name
        projectId (str): project id to delete. Used to check consistency
    Returns:
        dict: return response including delete status
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    shutil.rmtree(project_path)
    # os.removedirs(os.path.join(ROOT_PATH_PROJECT, project_name))

    return {"success": True, "message": "project deleted"}


@app.route("/api/project/load", methods=["GET", "POST"])
def load_project():
    """
    End-point to load project, this method retrieves expected project, concatenates
        information and returns to requester.

    Args (included into form's request) :
        projectName (str): project name to load, corresponding to sub-directory name
        projectId (str): project id to load. Used to check consistency
    Returns:
        dict: return project containing all information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.config_dict

    # transform data to interface with frontend
    project["config"] = transform_config_for_frontend(config, str(project_path))
    return project


@app.route("/api/project/save", methods=["GET", "POST"])
def save_project():
    """
    End-point to save project, take project parameters, refactor to save in json files.

    Args (included into form's request) :
        project (dict): project with all information to save
        projectId (str): project id to create. Used to check consistency
    Returns:
        dict: return project containing all information
    """
    project = json.loads(request.form["project"])

    project_loaded = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, project["name"]),
        project["id"],
    )
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
    config = transform_config_from_frontend(project["config"])
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

    return project


@app.route("/api/project/autoconnection", methods=["GET", "POST"])
def auto_connect_project():
    """
    Algorithm to auto-connect fmus together. Nominal auto-connection is the same
        name for input/output, should be improved with more complex algorithm

    Args (included into form's request) :
        projectName (str): project name, corresponding to sub-directory name
        projectId (str): project id. Used to check consistency
    Returns:
        dict: return connections list
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = transform_config_for_frontend(use_case_config.config_dict, project_path)
    fmus = config["fmus"]
    new_connections = []
    for index_fmu in range(len(fmus) - 1):
        for in_port in fmus[index_fmu]["inputPorts"]:
            for index_fmu_2 in range(index_fmu + 1, len(fmus)):
                outports = [
                    out_port
                    for out_port in fmus[index_fmu_2]["outputPorts"]
                    if out_port["name"] == in_port["name"]
                ]
                for out_port_2 in outports:
                    new_connections.append(
                        {
                            "source": {
                                "id": fmus[index_fmu_2]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": out_port_2["name"],
                            },
                            "target": {
                                "id": fmus[index_fmu]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": in_port["name"],
                            },
                        }
                    )
        for out_port in fmus[index_fmu]["outputPorts"]:
            for index_fmu_2 in range(index_fmu + 1, len(fmus)):
                inports = [
                    in_port
                    for in_port in fmus[index_fmu_2]["inputPorts"]
                    if in_port["name"] == out_port["name"]
                ]
                for in_port_2 in inports:
                    new_connections.append(
                        {
                            "source": {
                                "id": fmus[index_fmu]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": out_port["name"],
                            },
                            "target": {
                                "id": fmus[index_fmu_2]["id"],
                                "type": "fmu",
                                "unit": "",
                                "variable": in_port_2["name"],
                            },
                        }
                    )
    config["connections"] = new_connections
    config = transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return config["connections"]


@app.route("/api/fmu/information2", methods=["GET", "POST"])
def get_fmu_information():
    """
    Retrieve fmu information and format information as string (only variable table)
    Should be used to display copy or copy to clipboard

    Args (included into form's request) :
        projectName (str): project name, corresponding to sub-directory name
        projectId (str): project id. Used to check consistency
        fmu (dict): fmu for which retrieve information
    Returns:
        dict: return response object containing fmu information as string
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    information = fmu_utils.retrieve_fmu_info(
        os.path.join(project_path, fmu_info["path"])
    )
    string_result = "Category;name;start;type\n"
    for information_line in information:
        string_result += (
            str(information_line["category"])
            + ";"
            + str(information_line["name"])
            + ";"
            + str(information_line["start"])
            + ";"
            + str(information_line["type"])
            + "\n"
        )

    return {"success": True, "content": string_result}


@app.route("/api/fmu/information3", methods=["GET", "POST"])
def get_fmu_information_complete():
    """
    Retrieve all fmu information : model, cosimulation, variables

    Args (included into form's request) :
        projectName (str): project name, corresponding to sub-directory name
        projectId (str): project id. Used to check consistency
        fmu (dict): fmu for which retrieve information
    Returns:
        dict: return response object containing all fmu information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
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
                "stepSize": model_description.defaultExperiment.stepSize,
            }
            if model_description.defaultExperiment
            else None
        ),
        "coSimulation": {**model_description.coSimulation.__dict__},
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
                "start": modelVariable.start,
            }
            for modelVariable in model_description.modelVariables
            if modelVariable.causality != "local"
        ],
    }

    return my_model


@app.route("/api/fmu/delete", methods=["GET", "POST"])
def delete_fmu():
    """
    Delete fmu function. Remove file and all information on the fmu into config file :
        - fmu into "fmus" sections
        - all connections from or to fmu into "connections" section

    Args (included into form's request) :
        projectName (str): project name, corresponding to sub-directory name
        projectId (str): project id. Used to check consistency
        fmu (dict): fmu for which retrieve information
    Returns:
        return project containing all information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_info = json.loads(request.form["fmu"])

    # Delete fmu file
    os.remove(os.path.join(project_path, fmu_info["path"]))

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.config_dict

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
    config = transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return config


@app.route("/api/fmu/initialization/edit", methods=["GET", "POST"])
def edit_initialization_fmu():
    """
    Edit variable initialization into "fmus" section of the config file.
    1 request for each modified variable

    Args (included into form's request) :
        projectName (str): project name to edit, corresponding to sub-directory name
        projectId (str): project id to edit. Used to check consistency
        fmuId (str): fmu id to edit
        fmuName (str): fmu id to edit
        variable (dict): variable to edit, including id, name, value
    Returns:
        return project containing all information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmu_id = request.form["fmuId"]
    fmu_name = request.form["fmuName"]
    variable = json.loads(request.form["variable"])
    variable_name = variable["name"]
    variable_value = variable["initialization"]
    variable_type = variable["type"]

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.config_dict

    # Find fmu from fmus list
    fmus = config["fmus"]
    for fmu in config["fmus"]:
        if fmu["id"] == fmu_id and fmu["name"] == fmu_name:
            # Cast String value to correct type : Float, boolean or int
            if variable_type == "Real":
                fmu["initialization"][variable_name] = types.get_float(variable_value)
            if variable_type == "Integer":
                fmu["initialization"][variable_name] = types.get_int(variable_value)
            if variable_type == "Boolean":
                fmu["initialization"][variable_name] = types.get_boolean(variable_value)
            break

    config["fmus"] = fmus
    config = transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return project


@socketio.on("start_simulation")
def start_simulation(data: any):
    """
    Start simulation with web socket protocol, permits bidirectional communication
        while execution running

    Args :
        data (dict): variable containing all data to start simulation
            project (dict): project object containing all characteristics
            communication_time_step (str): step size for the simulation
            simulation_time (str): time of the simulation
    Returns:
        return progress messages as socket protocol all along the execution
    """
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

    emit("message", {"message": "Simulation start"})
    coordinator.run_simulation(communication_time_step, simulation_time, save_data=True)

    coordinator.save_results(os.path.join(project_path, "results_simulation.csv"))

    emit(
        "message",
        {
            "message": f"Simulation end with step size "
            f"{communication_time_step} and time {simulation_time}"
        },
    )


@app.route("/api/simulation/start", methods=["GET", "POST"])
def start_simulation_sync():
    """
    Start simulation with http protocol, used to test simulation execution with
        fixed parameters : time step=0.1s and time=30s

    Args (included into form's request) :
        projectName (str): project name, corresponding to sub-directory name
        projectId (str): project id. Used to check consistency
    Returns:
        return object with simulation execution result
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
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

    communication_time_step = 0.1
    coordinator.run_simulation(communication_time_step, 30, save_data=True)

    coordinator.save_results(os.path.join(project_path, "results_simulation.csv"))

    emit("message", {"message": "Simulation ended"}, broadcast=True)

    return {"succes": True}


@app.route("/api/fmu/edit", methods=["GET", "POST"])
def edit_fmu():
    """
    Edit information into "fmus" section of the config file.

    Args (included into form's request) :
        projectName (str): project name to edit, corresponding to sub-directory name
        projectId (str): project id to edit. Used to check consistency
        fmus (dict): dict containing all information on fmus section of the config
    Returns:
        return project containing all information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
    )
    project_path = os.path.join(ROOT_PATH_PROJECT, project["name"])
    fmus = json.loads(request.form["fmus"])

    use_case_config = ConfigParser(os.path.join(project_path, "config.json"))
    config = use_case_config.config_dict

    config["fmus"] = fmus
    config = transform_config_from_frontend(config)
    with open(os.path.join(project_path, "config.json"), "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)
    return project


@app.route("/api/fmu/upload", methods=["GET", "POST"])
def upload_file():
    """
    Upload fmu file, include into project directory and add fmu in "fmus" section
        of the config

    Args (included into form's request) :
        projectName (str): project name to edit, corresponding to sub-directory name
        projectId (str): project id to edit. Used to check consistency
        fmu (dict): fmu object to add in config
    Returns:
        return project containing all information
    """
    project = retrieve_project_from_params(
        os.path.join(ROOT_PATH_PROJECT, request.form["projectName"]),
        request.form["projectId"],
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


if __name__ == "__main__":
    socketio.run(app)
