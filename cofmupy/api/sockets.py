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
Flask sockets script.
Define all exposed WebSocket APIs
"""
from flask_socketio import emit

import os
import pprint
from .socket import socketio
from ..coordinator import Coordinator
from .config import ROOT_PATH_PROJECT


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
    print("\nSimulation end !!\n")
