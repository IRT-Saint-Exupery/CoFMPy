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
import networkx as nx
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock, Mock
import numpy as np
from cofmpy.graph_plotter import GraphPlotter
from pathlib import Path
import os


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
    "node_separation": 0.1,
    "node_radius": 0.05,
    "node_size": 40,
    "node_line_width": 3,
    "edge_linestyle": {"width": 3, "color": "#888"},
    "arrow_size": 0.02,
    "offset": 0.3,  # bezier curve offset
}


@pytest.fixture
def plotter():
    """Fixture to create and return a GraphPlotter instance."""
    plotter_obj = GraphPlotter()
    plotter_obj.config = DEFAULT_CONFIG
    return plotter_obj


@pytest.fixture
def mdgraph():
    """Fixture to create and return a GraphPlotter instance."""
    return nx.MultiGraph()


@pytest.fixture
def digraph():
    """Fixture to create and return a GraphPlotter instance."""
    return nx.DiGraph()


@pytest.fixture
def sample_graph():
    """Create a sample graph with nodes, edges and all the fields."""
    graph = nx.DiGraph()
    graph.add_node("A", id="A", name="Node A")
    graph.add_node("B", id="B", name="Node B")
    graph.add_edge("A", "B", label="A → B")

    node_list = [{"id": "A", "name": "Node A"}, {"id": "B", "name": "Node B"}]
    size_map = {"A": 1, "B": 0.5}

    return graph, node_list, size_map


def test_graphplotter_initialization(plotter):
    """Ensure GraphPlotter initializes correctly."""
    assert plotter.graph is None
    assert plotter.node_list is None
    assert plotter.size_map is None
    assert plotter.traces is None
    assert plotter.fig is None


def test_compute_bezier_curve():
    """Validate Bézier curve calculation."""

    expected_x = np.array([0, 0.5, 1, 1.5, 2])
    expected_y = np.array([0, 0.375, 0.5, 0.375, 0])
    p0, p1, p2 = (0, 0), (1, 1), (2, 0)

    x, y = GraphPlotter.compute_bezier_curve(p0, p1, p2, num_points=5)

    assert len(x) == 5
    assert len(y) == 5
    assert np.isclose(x, expected_x).all()
    assert np.isclose(y, expected_y).all()


@patch("plotly.graph_objects.Figure.write_html")
@patch("cofmpy.graph_plotter.datetime")
def test_save_plotly_figure(mock_datetime, mock_write_html, plotter):
    """Test saving a Plotly figure with a timestamped filename."""
    fig = go.Figure()

    mock_datetime.now.return_value.strftime.return_value = "240302_1530"

    filename = plotter.save_plotly_figure(fig, "test_plot", folder="/tmp")

    expected_filename = os.path.join("/tmp", "240302_1530_test_plot.html")

    # Split paths into components and compare them
    assert Path(filename).parts == Path(expected_filename).parts

    mock_write_html.assert_called_once_with(expected_filename)


def test_generate_figure(plotter, mdgraph):
    """Test generating a figure for a MultiGraph."""
    mdgraph.add_edge(1, 2, key=0, label="A")
    mdgraph.add_edge(2, 3, key=1, label="B")
    mdgraph.add_edge(3, 1, key=2, label="C")

    node_list = [{"id": 1}, {"id": 2}, {"id": 3}]
    size_map = {1: 0.1, 2: 0.2, 3: 0.3}

    expected_x = np.array(
        [
            -0.36375282,
            -0.32270249,
            -0.28220293,
            -0.24225415,
            -0.20285615,
            -0.16400893,
            -0.12571248,
            -0.08796681,
            -0.05077191,
            -0.01412779,
        ]
    )

    expected_y = np.array(
        [
            0.94468775,
            0.93855592,
            0.93174249,
            0.92424748,
            0.91607087,
            0.90721267,
            0.89767287,
            0.88745149,
            0.87654851,
            0.86496394,
        ]
    )

    figure = plotter.generate_figure(mdgraph, node_list, size_map)

    fig_x = np.array(figure.to_dict()["data"][1]["x"][:10])
    fig_y = np.array(figure.to_dict()["data"][1]["y"][:10])

    assert isinstance(figure, go.Figure)
    assert len(figure.data) > 0  # Ensure traces are generated

    assert np.isclose(fig_x, expected_x).all()
    assert np.isclose(fig_y, expected_y).all()


def test_generate_color_map_irt(plotter):
    """Test _generate_color_map when using 'irt' colormap."""
    plotter.conf = MagicMock()
    plotter.conf.cmap = "irt"  # Force 'irt' colormap

    elements = ["A", "B", "C"]
    color_map = plotter._generate_color_map(elements)

    expected_colors = [
        "rgba(148, 120, 255, 1.0)",
        "rgba(206, 195, 183, 1.0)",
        "rgba(0, 210, 77, 1.0)",
    ]

    assert isinstance(color_map, dict)
    assert set(color_map.keys()) == set(elements)
    assert list(color_map.values()) == expected_colors  # Ensure correct mapping


def test_generate_color_map_default(plotter):
    """Test _generate_color_map with a default colormap like 'viridis'."""
    plotter.conf = MagicMock()
    plotter.conf.cmap = "viridis"  # Use a standard matplotlib colormap

    elements = ["X", "Y", "Z"]
    color_map = plotter._generate_color_map(elements)

    assert isinstance(color_map, dict)
    assert set(color_map.keys()) == set(elements)
    assert all(color.startswith("rgba(") for color in color_map.values())  # Check RGBA format


def test_generate_color_map_empty(plotter):
    """Test _generate_color_map with an empty elements list."""
    plotter.conf = MagicMock()
    plotter.conf.cmap = "viridis"

    elements = []
    color_map = plotter._generate_color_map(elements)

    assert color_map == {}  # Should return an empty dictionary


@pytest.mark.parametrize("colormap", ["plasma", "coolwarm", "inferno"])
def test_generate_color_map_various_cmaps(colormap, plotter):
    """Test _generate_color_map with various matplotlib colormaps."""
    plotter.conf = MagicMock()
    plotter.conf.cmap = colormap

    elements = ["one", "two", "three", "four"]
    color_map = plotter._generate_color_map(elements)

    assert isinstance(color_map, dict)
    assert set(color_map.keys()) == set(elements)
    assert all(color.startswith("rgba(") for color in color_map.values())


def test_create_node_trace(sample_graph, plotter):
    """Test node trace creation."""
    graph, node_list, size_map = sample_graph
    plotter.node_positions = {"A": (1, 2), "B": (2, 3)}
    plotter.color_map = {"A": "rgba(255, 0, 0, 1)", "B": "rgba(0, 255, 0, 1)"}

    node_trace = plotter._create_node_trace(node_list[0], "A", size_map, plotter.color_map)
    assert isinstance(node_trace, go.Scatter)
    assert node_trace.marker["color"] == "rgba(255, 0, 0, 1)"
    assert node_trace.marker["size"] > 0


def test_create_edge_trace(plotter, mdgraph):
    """Test creating edge traces in a MultiGraph."""
    mdgraph.add_edge(1, 2, key=0, label="A")
    mdgraph.add_edge(2, 3, key=1, label="B")
    mdgraph.add_edge(3, 1, key=2, label="C")

    node_list = [{"id": 1}, {"id": 2}, {"id": 3}]
    size_map = {1: 0.1, 2: 0.2, 3: 0.3}

    plotter.generate_figure(mdgraph, node_list, size_map)  # Ensure node positions exist

    node_id = 1  # Pick a valid node ID from node_list
    edge_trace = plotter._create_edge_trace(node_id)

    assert edge_trace is not None
    assert len(edge_trace.x) > 0  # Ensure some edges are drawn
    assert len(edge_trace.y) > 0


def test_build_graph_lines(plotter, mdgraph):
    """Test edge line generation for a MultiGraph."""
    mdgraph.add_edge("A", "B", key=0, label="Edge AB")
    mdgraph.add_edge("B", "C", key=1, label="Edge BC")

    plotter.graph = mdgraph
    plotter.node_positions = {"A": (0, 0), "B": (1, 1), "C": (2, 2)}

    edge_x, edge_y, edge_labels = plotter._build_graph_lines("A")

    assert len(edge_x) > 0
    assert len(edge_y) > 0
    assert "Edge AB" in edge_labels


def test_control_point(plotter):
    """Test the _control_point method for correct Bezier control point calculation."""

    # Mock configuration with an offset factor
    plotter.conf = Mock()
    plotter.conf.offset = 0.3  # Example offset factor

    # Test case: Straight horizontal line
    x0, y0, x1, y1 = 0, 0, 4, 0
    expected_x = (x0 + x1) / 2 - (y1 - y0) * plotter.conf.offset  # 2.0
    expected_y = (y0 + y1) / 2 + (x1 - x0) * plotter.conf.offset  # 0.8
    assert plotter._control_point(x0, y0, x1, y1) == (expected_x, expected_y)

    # Test case: Straight vertical line
    x0, y0, x1, y1 = 0, 0, 0, 4
    expected_x = (x0 + x1) / 2 - (y1 - y0) * plotter.conf.offset  # -0.8
    expected_y = (y0 + y1) / 2 + (x1 - x0) * plotter.conf.offset  # 2.0
    assert plotter._control_point(x0, y0, x1, y1) == (expected_x, expected_y)

    # Test case: Diagonal line
    x0, y0, x1, y1 = 1, 1, 3, 3
    expected_x = (x0 + x1) / 2 - (y1 - y0) * plotter.conf.offset  # 2.0
    expected_y = (y0 + y1) / 2 + (x1 - x0) * plotter.conf.offset  # 2.0
    assert plotter._control_point(x0, y0, x1, y1) == (expected_x, expected_y)

    # Test case: Negative coordinates
    x0, y0, x1, y1 = -2, -2, 2, 2
    expected_x = (x0 + x1) / 2 - (y1 - y0) * plotter.conf.offset  # 0
    expected_y = (y0 + y1) / 2 + (x1 - x0) * plotter.conf.offset  # 0
    assert plotter._control_point(x0, y0, x1, y1) == (expected_x, expected_y)


def test_create_layout(plotter):
    """Test the creation of the layout."""

    buttons = [{"label": "All", "method": "update", "args": [{"visible": [True]}]}]

    layout = plotter._create_layout(buttons)

    # Extract actual updatemenus
    actual_updatemenus = layout.updatemenus
    expected_updatemenus = [{"buttons": buttons, "direction": "down", "showactive": True}]

    assert isinstance(layout, go.Layout)
    assert actual_updatemenus is not None
    assert len(actual_updatemenus) == 1  # Ensure there's one dropdown menu
    assert actual_updatemenus[0]["direction"] == "down"
    assert actual_updatemenus[0]["showactive"] is True

    # Ensure buttons structure matches
    actual_buttons = actual_updatemenus[0]["buttons"]
    assert len(actual_buttons) == len(buttons)
    assert all(actual_buttons[i]["label"] == buttons[i]["label"] for i in range(len(buttons)))


def test_generate_dropdown_options(plotter, mdgraph):
    """Test dropdown options for MultiGraph."""
    mdgraph.add_edge(1, 2, key=0, label="A")
    mdgraph.add_edge(2, 3, key=1, label="B")

    node_list = [{"id": 1}, {"id": 2}, {"id": 3}]
    size_map = {1: 0.1, 2: 0.2, 3: 0.3}

    # Generate figure to create traces
    plotter.generate_figure(mdgraph, node_list, size_map)

    # Now, call _generate_dropdown_options with valid traces
    buttons = plotter._generate_dropdown_options(plotter.traces)

    assert buttons is not None
    assert len(buttons) > 1
    assert buttons[0]["label"] == "All"


def test_create_scroll_button(plotter):
    """Test the create_scroll_button method for correct dropdown button generation."""

    label = "Zoom In"
    visible = [True, False, True]
    title = "Focused View"
    xrange = [0, 10]
    yrange = [5, 15]

    # Expected output
    expected_button = {
        "label": label,
        "method": "update",
        "args": [
            {"visible": visible},
            {
                "title": title,
                "xaxis": {"range": xrange, "showgrid": False, "showticklabels": False},
                "yaxis": {"range": yrange, "showgrid": False, "showticklabels": False},
            },
        ],
    }

    # Call method with full parameters
    button = plotter.create_scroll_button(label, visible, title, xrange, yrange)
    assert button == expected_button

    # Case when xrange and yrange are None
    expected_button_no_range = {
        "label": label,
        "method": "update",
        "args": [
            {"visible": visible},
            {
                "title": title,
                "xaxis": {"range": None, "showgrid": False, "showticklabels": False},
                "yaxis": {"range": None, "showgrid": False, "showticklabels": False},
            },
        ],
    }

    button_no_range = plotter.create_scroll_button(label, visible, title)
    assert button_no_range == expected_button_no_range
