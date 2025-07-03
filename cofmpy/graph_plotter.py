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
The GraphPlotter class is responsible for generating an interactive
graph visualization based on input node and edge data.
It uses NetworkX to manage node positioning and Plotly for graph rendering.
It supports display configuration from PlotConfig class.

Example Usage:
    ```
    graph = nx.MultiGraph()

    graph.add_edge(1, 2, key=0, label="A")
    graph.add_edge(2, 3, key=1, label="B")
    graph.add_edge(3, 1, key=2, label="C")

    node_list = [{"id": 1}, {"id": 2}, {"id": 3}]

    size_map = {1: 0.1, 2: 0.2, 3: 0.3}

    plotter = GraphPlotter()
    figure = plotter.generate_figure(graph, node_list, size_map)

    figure.show()
    ```
"""

import os
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go

DEFAULT_CONFIG = {
    "seed": 42,
    "go_margin": {"b": 10, "l": 20, "r": 20, "t": 40},
    "height": 400,
    "cmap": "irt",
    "zoom_factor": 0.1,  # area around center-of-zoom
    "font_size": 16,
    "hide_axis_params": {
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "gridcolor": "white",
        "zerolinecolor": "white",
    },
    "node_radius": 0.05,
    "node_size": 40,
    "node_line_width": 3,
    "edge_linestyle": {"width": 3, "color": "#888"},
    "arrow_size": 0.02,
    "offset": 0.3,  # bezier curve offset
}


@dataclass
class Keys:
    """Keys for accessing nodes and edges dictionaries"""

    node_id: str = "id"
    name: str = "name"


class GraphPlotter:
    """
    A class responsible for generating and plotting a graph using Plotly.

    This class takes a networkx graph along with node attributes and generates
    a visual representation using Plotly. It computes node positions, assigns
    colors, and creates traces for nodes and edges.

    Custom dependencies: the method plot_graph uses
    """

    def __init__(self):
        """
        Initializes the GraphPlotter with configuration and key mappings.
        """
        self.keys = Keys()
        self.config = DEFAULT_CONFIG

        self.graph = None
        self.node_list = None
        self.size_map = None
        self.node_positions = None
        self.color_map = None
        self.traces = None
        self.buttons = None
        self.layout = None
        self.fig = None

    @staticmethod
    def create_scroll_button(
        label: str,
        visible: List[bool],
        title: str = "",
        xrange: Optional[List[Union[int, float]]] = None,
        yrange: Optional[List[Union[int, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a Plotly dropdown button configuration for scrolling within the visualization.

        Args:
            label (str): The text displayed on the dropdown button.
            visible (List[bool]): A list indicating which traces should be visible.
            title (str, optional): The title of the plot. Defaults to an empty string.
            xrange (Optional[List[Union[int, float]]], optional): The x-axis range [min, max].
                Defaults to None.
            yrange (Optional[List[Union[int, float]]], optional): The y-axis range [min, max].
                Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary representing the button configuration for Plotly.
        """
        return {
            "label": label,
            "method": "update",
            "args": [
                {"visible": visible},
                {
                    "title": title,
                    "xaxis": {
                        "range": xrange,
                        "showgrid": False,
                        "showticklabels": False,
                    },
                    "yaxis": {
                        "range": yrange,
                        "showgrid": False,
                        "showticklabels": False,
                    },
                },
            ],
        }

    @staticmethod
    def compute_bezier_curve(
        pt_0: Tuple[float, float],
        pt_1: Tuple[float, float],
        pt_2: Tuple[float, float],
        num_points: int = 50,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes a quadratic Bezier curve given three control points.

        Args:
            pt_0: The start point (x, y).
            pt_1: The control point (x, y).
            pt_2: The end point (x, y).
            num_points: Number of points to generate along the curve.

        Returns:
            Tuple of NumPy arrays (x values, y values) representing the curve.
        """
        t_lin = np.linspace(0, 1, num_points)

        x_0, y_0 = pt_0
        x_1, y_1 = pt_1
        x_2, y_2 = pt_2
        t_0, t_1, t_2 = (1 - t_lin) ** 2, 2 * (1 - t_lin) * t_lin, t_lin**2

        bezier_x = t_0 * x_0 + t_1 * x_1 + t_2 * x_2
        bezier_y = t_0 * y_0 + t_1 * y_1 + t_2 * y_2

        return bezier_x, bezier_y

    @staticmethod
    def save_plotly_figure(fig: go.Figure, name: str, folder: str = ".") -> str:
        """
        Saves a Plotly figure as an HTML file with a timestamped filename.

        Args:
            fig (Figure): The Plotly figure to save.
            name (str): The base name for the saved file.
            folder (str, optional): The folder where the file will be saved. Defaults to
                the current directory.

        Returns:
            str: The full path of the saved file.
        """
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        filename = os.path.join(folder, f"{timestamp}_{name}.html")
        fig.write_html(filename)
        print(f"Figure saved to {filename}")
        return filename

    def generate_figure(
        self,
        graph: nx.Graph,
        node_list: List[Dict[str, any]],
        size_map: Dict[str, float],
    ) -> go.Figure:
        """
        Generates a Plotly figure representing the given graph.

        Computes node positions, assigns colors, and creates traces for both
        nodes and edges.

        Args:
            graph (nx.Graph): The networkx graph to visualize.
            node_list (list): A list of nodes containing attributes.
            size_map (dict): A dictionary mapping node IDs to scaling factors.

        Returns:
            go.Figure: The generated Plotly figure containing the graph visualization.
        """

        self.graph = graph
        self.node_list = node_list
        self.size_map = size_map
        self.node_positions = nx.spring_layout(self.graph, seed=self.config["seed"])

        # Generate color map
        self.color_map = self._generate_color_map(
            [n[self.keys.node_id] for n in self.node_list]
        )

        # Generate figure
        self.traces = self._generate_traces()
        self.buttons = self._generate_dropdown_options(self.traces)
        self.layout = self._create_layout(self.buttons)
        self.fig = go.Figure(data=self.traces, layout=self.layout)

        return self.fig

    def _generate_color_map(self, elements: List[str]) -> Dict[str, str]:
        """
        Generates a distinct color map for a given list of elements.

        The function assigns each element a unique RGBA color derived from a colormap.

        Args:
            elements (List[str]): A list of unique elements to be assigned colors.

        Returns:
            Dict[str, str]: A dictionary mapping each element to an RGBA color string.
        """
        num_colors = len(elements)

        if self.config["cmap"].lower() == "irt":
            custom_colors = ["#9478ff", "#cec3b7", "#00d24d"]
            cmap = LinearSegmentedColormap.from_list("irt", custom_colors, N=num_colors)
        else:
            cmap = plt.get_cmap(self.config["cmap"])

        # Generate colors using evenly spaced points in the colormap
        colors = [cmap(i) for i in np.linspace(0, 1, num_colors)]

        # Map each element to its respective RGBA color
        color_map = {
            element: f"rgba({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}, {c[3]})"
            for element, c in zip(elements, colors)
        }

        return color_map

    def _generate_traces(self) -> List[go.Scatter]:
        """
        Creates Plotly traces for both nodes and edges.

        Iterates through the node list, generating traces for individual nodes
        and their corresponding edges.

        Returns:
            List[go.Scatter]: A list of Plotly scatter traces representing nodes and edges.
        """
        traces = []

        for node in self.node_list:
            node_id = node[self.keys.node_id]
            traces.append(
                self._create_node_trace(node, node_id, self.size_map, self.color_map)
            )
            traces.append(self._create_edge_trace(node_id))

        return traces

    def _create_node_trace(
        self,
        node: Dict[str, Any],
        node_id: str,
        size_map: Dict[str, str],
        color_map: Dict[str, str],
    ) -> go.Scatter:
        """
        Creates a Plotly scatter trace for a single node.

        Args:
            node (Dict[str, Any]): Dictionary containing node metadata.
            node_id (str): Unique identifier of the node.
            size_map (Dict[str, str]): Mapping of node IDs to its size factor.
            color_map (Dict[str, str]): Mapping of node IDs to their respective colors.

        Returns:
            go.Scatter: A Plotly Scatter trace representing the node.
        """
        x_coord, y_coord = self.node_positions[node_id]

        hover_text = "<br>".join([f"{k}: {v}" for k, v in node.items()])

        node_size = self.config["node_size"] * size_map[node_id]

        return go.Scatter(
            x=[x_coord],
            y=[y_coord],
            mode="markers+text",
            text=node.get(self.keys.name, node_id),
            textposition="top center",
            hovertext=[hover_text],
            hoverinfo="text",
            marker={
                "showscale": False,
                "size": node_size,
                "line_width": self.config["node_line_width"],
                "color": color_map[node_id],
            },
            name=node.get(self.keys.name, node_id),
        )

    def _create_edge_trace(self, node_id: str) -> go.Scatter:
        """
        Creates a Plotly scatter trace for edges connected to a given node.

        Args:
            node_id (str): The ID of the node for which edges should be created.

        Returns:
            go.Scatter: A Plotly Scatter trace representing edges.
        """
        edge_x, edge_y, edge_labels = self._build_graph_lines(node_id)

        return go.Scatter(
            x=edge_x,
            y=edge_y,
            line=self.config["edge_linestyle"],
            hoverinfo="text",
            mode="lines",
            text=edge_labels,
            hovertext=edge_labels,
            showlegend=False,
        )

    def _build_graph_lines(
        self, node_id: Any
    ) -> Tuple[List[float], List[float], List[str]]:
        """
        Constructs graph edges with curved paths and arrows using self.graph.edges.

        Args:
            node_id (Any): The ID of the node whose edges are to be drawn.

        Returns:
            Tuple[List[float], List[float], List[str]]: Edge coordinates and labels.
        """
        edge_x, edge_y, edge_labels = [], [], []

        for source, target, _, data in self.graph.edges(node_id, data=True, keys=True):
            # Extract node positions
            (x_0, y_0), (x_1, y_1) = (
                self.node_positions[source],
                self.node_positions[target],
            )

            # Compute Bezier curve
            curve_x, curve_y = self.compute_bezier_curve(
                (x_0, y_0), self._control_point(x_0, y_0, x_1, y_1), (x_1, y_1)
            )
            edge_x.extend(curve_x.tolist() + [None])
            edge_y.extend(curve_y.tolist() + [None])
            edge_labels.extend([data["label"]] * len(curve_x) + [None])

            # Append arrowhead
            if len(curve_x) > 1:
                direction = np.array(
                    [curve_x[-1] - curve_x[-2], curve_y[-1] - curve_y[-2]]
                )
                norm = np.linalg.norm(direction)
                if norm != 0:
                    direction /= norm
                    tip = (
                        np.array([curve_x[-1], curve_y[-1]])
                        - direction * self.config["node_radius"] * 0.8
                    )
                    end = tip - direction * self.config["arrow_size"]
                    perp = (
                        np.array([-direction[1], direction[0]])
                        * self.config["arrow_size"]
                    )
                    left, right = end + perp, end - perp

                    edge_x.extend([tip[0], left[0], right[0], tip[0], None])
                    edge_y.extend([tip[1], left[1], right[1], tip[1], None])
                    edge_labels.extend(["", "", "", "", None])

        return edge_x, edge_y, edge_labels

    def _control_point(
        self, x_0: float, y_0: float, x_1: float, y_1: float
    ) -> Tuple[float, float]:
        """
        Computes the control point for a quadratic Bezier curve between two points.

        The control point is calculated such that the curve bends smoothly based on
        an offset factor (`self.config["offset"]`). The offset determines how much the
        curve deviates from a straight line.

        Args:
            x_0 (float): X-coordinate of the starting point.
            y_0 (float): Y-coordinate of the starting point.
            x_1 (float): X-coordinate of the ending point.
            y_1 (float): Y-coordinate of the ending point.

        Returns:
            Tuple[float, float]: The (x, y) coordinates of the control point.
        """
        return (
            (x_0 + x_1) / 2 - (y_1 - y_0) * self.config["offset"],
            (y_0 + y_1) / 2 + (x_1 - x_0) * self.config["offset"],
        )

    def _generate_dropdown_options(self, traces: List[go.Scatter]) -> List[Dict]:
        """
        Generates dropdown buttons for interactive zooming on nodes.

        The dropdown menu allows users to:
        - Show all nodes (default view).
        - Zoom in on a specific node by adjusting the x/y axis ranges.

        Args:
            traces (List[go.Scatter]): List of Plotly traces to be controlled by the dropdown.

        Returns:
            List[Dict]: A list of dropdown button configurations for Plotly.
        """
        buttons = [self.create_scroll_button("All", [True] * len(traces))]

        for node in self.node_list:
            node_id = node[self.keys.node_id]
            x_coord, y_coord = self.node_positions[node_id]
            zoom_factor = self.config["zoom_factor"]
            x_range = [x_coord - zoom_factor, x_coord + zoom_factor]
            y_range = [y_coord - zoom_factor, y_coord + zoom_factor]

            buttons.append(
                self.create_scroll_button(
                    label=f"{node_id}",
                    visible=[True] * len(traces),
                    title=f"Zoom on {node_id}",
                    xrange=x_range,
                    yrange=y_range,
                )
            )

        return buttons

    def _create_layout(self, buttons: List[Dict]) -> go.Layout:
        """
        Creates the layout configuration for the Plotly figure.

        This method defines:
        - Background color
        - Hover behavior
        - Font settings
        - Axis visibility
        - Dropdown menu for zooming options

        Args:
            buttons (List[Dict]): Dropdown buttons for interactive node zooming.

        Returns:
            go.Layout: The layout configuration for the figure.
        """
        return go.Layout(
            showlegend=True,
            hovermode="closest",
            margin=self.config["go_margin"],
            plot_bgcolor="white",
            font={"size": self.config["font_size"]},
            xaxis=self.config["hide_axis_params"],
            yaxis=self.config["hide_axis_params"],
            updatemenus=[{"buttons": buttons, "direction": "down", "showactive": True}],
            height=self.config["height"],
        )
