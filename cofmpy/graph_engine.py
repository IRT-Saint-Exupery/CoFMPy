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
"""
The GraphEngine class is responsible for creating a graph representation of the
co-simulation diagram.

The graph consists of nodes representing either FMUs or symbolic nodes (data sources and
sinks). Directed edges represent the connections between FMUs or between an FMU and a
source/sink. The class provides methods to compute the execution order of nodes, and to
plot the graph (using GraphPlotter class). The execution order, determined by strongly
connected components (SCCs), is used by the Master algorithm to schedule the simulation steps.

The GraphEngine uses the NetworkX library to build and manipulate the graph.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Set

import networkx as nx
import plotly.graph_objects as go

from .graph_plotter import GraphPlotter


@dataclass
class Keys:
    """Keys for accessing FMU and connections dictionaries"""

    # FMU keys
    fmu_id: str = "id"
    name: str = "name"
    path: str = "path"
    stepsize: str = "stepsize"

    # Connection keys
    source: str = "source"
    target: str = "target"
    uri: str = "uri"
    variable: str = "variable"
    unit: str = "unit"


class GraphEngine:
    """
    GraphEngine is a class that represents a graph structure based on
    * FMUs and/or symbolic nodes
    * connections (namely edges)
    It uses networkx library to build and manipulate the graph.

    Custom dependencies: the method plot_graph uses GraphPlotter
    """

    def __init__(
        self,
        fmu_list: List[Dict],
        symbolic_nodes: List[Dict],
        conn_list: List[Dict],
        edge_sep: str = " -> ",
    ) -> None:
        """
        Initialize the GraphEngine instance, set up the FMU and connection lists,
        and construct the graph.

        Args:
            fmu_list (List[Dict]): List of FMU data (each FMU represented as a
                dictionary).
            symbolic_nodes (List[Dict]): List of symbolic nodes (each node represented
                as a dictionary).
            conn_list (List[Dict]): List of connections (each connection represented as
                a dictionary).
            edge_sep (str, optional): Separator used for edge labels.
                Default is " -> ".
        """

        self.fmu_list = fmu_list
        self.symbolic_nodes = symbolic_nodes
        self.conn_list = conn_list
        self.edge_sep = edge_sep
        self.keys = Keys()
        self.color_map = {}

        # Build Graph
        self.graph, self.fmu_types = self._create_graph()

        # Create connections and get order
        self.connections = self._name_connections()
        self.sequence_order = self._get_order()

    def _create_graph(self) -> nx.MultiDiGraph:
        """
        Creates a directed multigraph (`nx.MultiDiGraph`) representing FMUs (Functional
        Mock-up Units) and their connections.

        The method:
        1. Initializes an empty directed multigraph (`self.graph`).
        2. Adds FMU and symbolic nodes with metadata.
        3. Adds directed edges representing connections between FMUs.
        4. Stores variable-unit mappings in `self.units`.
        5. Logs a warning if units are inconsistent across a connection.

        Returns:
            nx.MultiDiGraph: The generated directed multigraph.
        """
        self.graph = nx.MultiDiGraph()
        self.units = {}  # Stores mapping: variable -> unit

        # Add FMUs and symbolic nodes
        for fmu in self.fmu_list:
            self._add_node(fmu, node_type="fmu")

        for node in self.symbolic_nodes:
            self._add_node(node, node_type="symbolic")

        # Add connections
        for connection in self.conn_list:
            self._add_edge(connection)

        self.fmu_types = nx.get_node_attributes(self.graph, "type")

        return self.graph, self.fmu_types

    def _add_node(self, node_data: Dict[str, Any], node_type: str) -> None:
        """
        Adds a node to the directed graph, representing either an FMU or a symbolic node.

        Args:
            node_data (Dict[str, Any]): A dictionary containing node attributes.
            node_type (str): Type of the node, either `"fmu"` or `"symbolic"`.

        Node Attributes:
            - `label` (str): The node name or ID.
            - `path` (str, optional): The file path for FMUs.
            - `steptime` (float, optional): Step time of the FMU.
            - `type` (str): `"fmu"` or `"symbolic"`, used for classification.
        """
        node_id = node_data.get(self.keys.fmu_id)
        node_name = node_data.get(self.keys.name, node_id)

        self.graph.add_node(
            node_id,
            label=node_name,
            path=node_data.get(self.keys.path),
            steptime=node_data.get(self.keys.stepsize),
            type=node_type,
        )

    def _add_edge(self, connection: Dict[str, Any]) -> None:
        """
        Adds a directed edge between two nodes in the graph, representing a connection
        between FMUs or symbolic nodes.

        Args:
            connection (Dict[str, Any]): A dictionary containing connection details.

        Edge Attributes:
            - `label` (str): A short label for the edge (e.g., variable names).
            - `full_label` (str): A more detailed label including source, target, and units.

        The method also stores variable-unit mappings and logs warnings for missing
        edges endpoints and inconsistent units.
        """
        # Extract source and target FMU IDs
        source = connection.get(self.keys.source, {}).get(self.keys.fmu_id)
        target = connection.get(self.keys.target, {}).get(self.keys.fmu_id)

        if source is None or target is None:
            logging.warning(
                "Skipping edge with missing source (%s) or target (%s).",
                *(source, target),
            )
            return  # Avoid adding an invalid edge

        # Extract variable names and units
        src_var = connection.get(self.keys.source, {}).get(
            self.keys.variable, "Unknown"
        )
        tgt_var = connection.get(self.keys.target, {}).get(
            self.keys.variable, "Unknown"
        )
        src_unit = connection.get(self.keys.source, {}).get(self.keys.unit, "N/A")
        tgt_unit = connection.get(self.keys.target, {}).get(self.keys.unit, "N/A")

        # Store variable-unit mappings
        self.units[src_var] = src_unit
        self.units[tgt_var] = tgt_unit

        # Define edge labels
        label = self._name_edge(src_var, tgt_var)
        full_label = (
            f"{source} ({src_var} / {src_unit}) → {target} ({tgt_var} / {tgt_unit})"
        )

        # Add edge to the graph
        self.graph.add_edge(source, target, label=label, full_label=full_label)

        # Log a warning if units are inconsistent
        if src_unit != tgt_unit:
            logging.warning(
                "Inconsistent units in '%s': %s -> %s.", *(label, src_unit, tgt_unit)
            )

    def _get_order(self) -> List[Set]:
        """
        Computes the execution order of nodes in the directed graph by:
        1. Identifying strongly connected components (SCCs).
        2. Creating a condensed graph where each SCC is a single node.
        3. Performing a topological sort on the condensed graph.

        Returns:
            List[Set[str]]: A list of sets, each containing nodes in execution order.
        """

        # Strongly connected components
        sccs = list(nx.strongly_connected_components(self.graph))

        # Create the condensed graph
        condensed_graph = nx.condensation(self.graph)

        # Get the topological order of the condensed graph
        topo_order: List[int] = list(nx.topological_sort(condensed_graph))

        # Order nodes in sets
        order = [
            sccs[scc] if isinstance(sccs[scc], set) else {sccs[scc]}
            for scc in topo_order
        ]

        # Filter out sets containing symbolic nodes
        node_types = nx.get_node_attributes(self.graph, "type")
        order = [s for s in order if all(node_types[node] == "fmu" for node in s)]

        return order

    def _name_connections(self) -> Dict[str, str]:
        """
        Constructs a mapping of connections between FMUs based on the graph's edges.

        The method:
        1. Iterates over all outgoing edges in the directed graph.
        2. Extracts source and target FMUs.
        3. Retrieves the connection label and extracts variable names.
        4. Builds a dictionary mapping the formatted source variable name to the target
           variable name.

        Attributes:
            self.graph (nx.MultiDiGraph): The directed graph representing FMUs and their
                connections.
            self.edge_sep (str): The separator used in edge labels to split variable
                names.

        Returns:
            Dict[str, str]: A mapping where the key is the formatted source variable,
                            and the value is the corresponding formatted target
                            variable.
        """
        connections = {}

        for source_fmu, target_fmu in self.graph.out_edges(data=False):
            # Retrieve edge label
            edge_data = self.graph.get_edge_data(source_fmu, target_fmu)
            if not edge_data:
                continue  # Skip if no edge data found

            label = edge_data[0]["label"]

            # Extract source and target variable names
            source_var, target_var = label.split(self.edge_sep)

            # Map the connection using formatted names
            connections[self._name_edge(source_fmu, source_var)] = self._name_edge(
                target_fmu, target_var
            )

        return connections

    def _name_edge(self, name1: str, name2: str) -> str:
        """
        Creates a formatted edge name by joining two names with a separator.

        Args:
            name1 (str): The first name (e.g., source).
            name2 (str): The second name (e.g., target).

        Returns:
            str: A formatted string representing the edge.
        """
        return f"{name1}{self.edge_sep}{name2}"

    def plot_graph(self, savefig: bool = False) -> go.Figure:
        """
        Plot a graph representation of the co-simulation diagram.

        This method generates a Plotly figure showing nodes and their connections.
        It uses NetworkX for node positioning and Plotly for rendering the graph.

        Args:
            savefig (bool, optional): Whether to save the figure as an HTML file. Defaults to False.

        Returns:
            go.Figure: The Plotly figure object representing the co-simulation diagram.
        """

        plotter = GraphPlotter()

        size_map = {k: 1 if v == "fmu" else 0.2 for k, v in self.fmu_types.items()}

        fig = plotter.generate_figure(
            self.graph, self.fmu_list + self.symbolic_nodes, size_map
        )

        self.color_map = plotter.color_map

        if savefig:
            plotter.save_plotly_figure(fig, "cosim_diagram")

        return fig
