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
import logging
import pytest
import networkx as nx
from unittest.mock import patch
from cofmpy.graph_engine import GraphEngine


@pytest.fixture
def sample_data():
    fmu_list = [
        {"id": "fmu1", "name": "FMU 1", "path": "path/to/fmu1", "stepsize": "0.1"},
        {"id": "fmu2", "name": "FMU 2", "path": "path/to/fmu2", "stepsize": "0.2"},
    ]
    symbolic_nodes = [{"id": "sym1", "name": "Symbolic 1"}]
    conn_list = [
        {
            "source": {"id": "fmu1", "variable": "var1", "unit": "m"},
            "target": {"id": "fmu2", "variable": "var2", "unit": "m"},
        }
    ]
    return fmu_list, symbolic_nodes, conn_list


def test_graph_engine_initialization():
    fmu_list = [{"id": 1, "type": "A"}, {"id": 2, "type": "B"}]
    symbolic_nodes = [{"id": 3, "type": "symbolic"}]
    conn_list = [{"source": 1, "target": 3}, {"source": 2, "target": 3}]

    with patch.object(
        GraphEngine, "_create_graph", return_value=("mock_graph", "mock_fmu_types")
    ) as mock_create_graph, patch.object(
        GraphEngine, "_name_connections", return_value="mock_connections"
    ) as mock_name_connections, patch.object(
        GraphEngine, "_get_order", return_value="mock_order"
    ) as mock_get_order:

        engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

        # Assertions
        assert engine.fmu_list == fmu_list
        assert engine.symbolic_nodes == symbolic_nodes
        assert engine.conn_list == conn_list
        assert engine.edge_sep == " -> "  # Default separator
        assert engine.graph == "mock_graph"
        assert engine.fmu_types == "mock_fmu_types"
        assert engine.connections == "mock_connections"
        assert engine.sequence_order == "mock_order"

        # Verify that the mocked methods were called
        mock_create_graph.assert_called_once()
        mock_name_connections.assert_called_once()
        mock_get_order.assert_called_once()


def test_graph_engine_empty_inputs():
    with patch.object(
        GraphEngine, "_create_graph", return_value=(nx.MultiDiGraph(), {})
    ):
        engine = GraphEngine([], [], [])

        # Ensure graph is created
        assert engine.graph is not None
        assert engine.graph.is_directed()  # Should not raise AttributeError
        assert engine.fmu_list == []
        assert engine.symbolic_nodes == []
        assert engine.conn_list == []
        assert engine.edge_sep == " -> "


def test_create_graph(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    assert isinstance(engine.graph, nx.MultiDiGraph)
    assert len(engine.graph.nodes) == 3  # 2 FMUs + 1 symbolic node
    assert len(engine.graph.edges) == 1  # 1 connection

    # Check node attributes
    assert engine.graph.nodes["fmu1"]["type"] == "fmu"
    assert engine.graph.nodes["sym1"]["type"] == "symbolic"


def test_add_fmu_node():
    """Test adding an FMU node to the graph."""
    engine = GraphEngine([], [], [])  # Initialize with empty lists
    node_data = {
        engine.keys.fmu_id: "fmu_1",
        engine.keys.name: "FMU Node 1",
        engine.keys.path: "/path/to/fmu",
        engine.keys.stepsize: 0.01,
    }

    engine._add_node(node_data, node_type="fmu")

    assert "fmu_1" in engine.graph.nodes
    node_attrs = engine.graph.nodes["fmu_1"]

    assert node_attrs["label"] == "FMU Node 1"
    assert node_attrs["path"] == "/path/to/fmu"
    assert node_attrs["steptime"] == 0.01
    assert node_attrs["type"] == "fmu"


def test_add_symbolic_node():
    """Test adding a symbolic node to the graph."""
    engine = GraphEngine([], [], [])
    node_data = {engine.keys.fmu_id: "symbolic_1", engine.keys.name: "Symbolic Node 1"}

    engine._add_node(node_data, node_type="symbolic")

    assert "symbolic_1" in engine.graph.nodes
    node_attrs = engine.graph.nodes["symbolic_1"]

    assert node_attrs["label"] == "Symbolic Node 1"
    assert node_attrs.get("path") is None  # Should not exist
    assert node_attrs.get("steptime") is None  # Should not exist
    assert node_attrs["type"] == "symbolic"


def test_add_node_missing_name():
    """Test adding a node when the name is missing."""
    engine = GraphEngine([], [], [])
    node_data = {engine.keys.fmu_id: "node_1"}

    engine._add_node(node_data, node_type="fmu")

    assert "node_1" in engine.graph.nodes
    node_attrs = engine.graph.nodes["node_1"]

    assert node_attrs["label"] == "node_1"  # Should fall back to ID
    assert node_attrs.get("path") is None
    assert node_attrs.get("steptime") is None
    assert node_attrs["type"] == "fmu"


def test_add_valid_edge(caplog):
    """Test adding a valid edge between two nodes."""
    engine = GraphEngine([], [], [])

    # Add nodes to the graph first
    engine.graph.add_node("A", label="Node A")
    engine.graph.add_node("B", label="Node B")

    connection = {
        engine.keys.source: {
            engine.keys.fmu_id: "A",
            engine.keys.variable: "var1",
            engine.keys.unit: "m",
        },
        engine.keys.target: {
            engine.keys.fmu_id: "B",
            engine.keys.variable: "var2",
            engine.keys.unit: "m",
        },
    }

    engine._add_edge(connection)

    assert engine.graph.has_edge("A", "B")

    # Fix: Access the first edge's attributes properly
    edge_attrs = list(engine.graph["A"]["B"].values())[
        0
    ]  # Get the first edge's attributes

    assert "label" in edge_attrs
    assert "full_label" in edge_attrs
    assert edge_attrs["label"] == engine._name_edge("var1", "var2")
    assert edge_attrs["full_label"] == "A (var1 / m) → B (var2 / m)"

    # Ensure no warnings for unit consistency
    with caplog.at_level(logging.WARNING):
        assert not any(
            "Inconsistent units" in record.message for record in caplog.records
        )


def test_add_edge_missing_source_or_target(caplog):
    """Test that edges with missing source or target nodes are skipped safely."""
    engine = GraphEngine([], [], [])

    # Missing source
    connection_missing_source = {
        engine.keys.target: {
            engine.keys.fmu_id: "B",
            engine.keys.variable: "var2",
            engine.keys.unit: "m",
        },
    }

    with caplog.at_level(logging.WARNING):
        engine._add_edge(connection_missing_source)

    assert not engine.graph.has_edge(None, "B")  # Edge should not exist
    assert any(
        "Skipping edge with missing source" in record.message
        for record in caplog.records
    )

    # Missing target
    connection_missing_target = {
        engine.keys.source: {
            engine.keys.fmu_id: "A",
            engine.keys.variable: "var1",
            engine.keys.unit: "m",
        },
    }

    with caplog.at_level(logging.WARNING):
        engine._add_edge(connection_missing_target)

    assert not engine.graph.has_edge("A", None)  # Edge should not exist
    assert any(
        "Skipping edge with missing source" in record.message
        for record in caplog.records
    )


def test_add_edge_inconsistent_units(caplog):
    """Test adding an edge with inconsistent units, expecting a warning."""
    engine = GraphEngine([], [], [])

    # Add nodes
    engine.graph.add_node("A", label="Node A")
    engine.graph.add_node("B", label="Node B")

    connection = {
        engine.keys.source: {
            engine.keys.fmu_id: "A",
            engine.keys.variable: "var1",
            engine.keys.unit: "m",
        },
        engine.keys.target: {
            engine.keys.fmu_id: "B",
            engine.keys.variable: "var2",
            engine.keys.unit: "s",
        },
    }

    with caplog.at_level(logging.WARNING):
        engine._add_edge(connection)

        # Check if the warning was logged
        assert any("Inconsistent units" in record.message for record in caplog.records)


def test_missing_edge_data(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    # Manually remove edge data
    engine.graph.remove_edge("fmu1", "fmu2")

    # Recompute connections to trigger the edge_data check
    connections = engine._name_connections()

    # Ensure missing edge does not cause an error and returns an empty mapping
    assert connections == {}


def test_get_order(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    order = engine.sequence_order
    assert len(order) == 2  # Two FMUs
    assert order[0] == {"fmu1"}
    assert order[1] == {"fmu2"}


def test_name_connections(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    connections = engine.connections
    assert "fmu1 -> var1" in connections
    assert connections["fmu1 -> var1"] == "fmu2 -> var2"


def test_name_edge():
    """Test that _name_edge correctly formats edge names with the separator."""
    engine = GraphEngine([], [], [], edge_sep=" -> ")  # Custom separator

    assert engine._name_edge("A", "B") == "A -> B"
    assert engine._name_edge("var1", "var2") == "var1 -> var2"

    # Edge cases
    assert engine._name_edge("", "B") == " -> B"  # Empty source name
    assert engine._name_edge("A", "") == "A -> "  # Empty target name
    assert engine._name_edge("", "") == " -> "  # Both names empty

    # Different separator
    engine.edge_sep = " | "
    assert engine._name_edge("X", "Y") == "X | Y"


def test_plot_graph(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    fig = engine.plot_graph()
    assert fig is not None


def test_plot_graph_with_save(sample_data):
    fmu_list, symbolic_nodes, conn_list = sample_data
    engine = GraphEngine(fmu_list, symbolic_nodes, conn_list)

    with patch("cofmpy.graph_plotter.GraphPlotter.save_plotly_figure") as mock_save:
        engine.plot_graph(savefig=True)
        mock_save.assert_called_once_with(mock_save.call_args[0][0], "cosim_diagram")
