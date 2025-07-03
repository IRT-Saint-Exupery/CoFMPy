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
import os
import tempfile
import unittest

from cofmpy.coordinator import Coordinator


class CoordinatorCheck(unittest.TestCase):
    def setUp(self):
        self.toto = 1
        self.test_get_results_results = {
            ("source", "V"): [
                0.0,
                -4.898587196589413e-14,
                -9.797174393178826e-14,
                -4.3117471020172245e-13,
                -1.9594348786357651e-13,
                3.928773447456944e-14,
                -8.623494204034449e-13,
                -6.27118198065299e-13,
                -3.9188697572715303e-13,
                -1.5665575338900706e-13,
            ],
            ("resistor", "I"): [
                0.0,
                -9.797174393178826e-14,
                -1.9594348786357651e-13,
                -8.623494204034449e-13,
                -3.9188697572715303e-13,
                7.857546894913887e-14,
                -1.7246988408068898e-12,
                -1.254236396130598e-12,
                -7.837739514543061e-13,
                -3.1331150677801413e-13,
            ],
            "time": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90],
        }

    def test_start(self):
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        self.assertEqual(
            my_coordinator.graph_engine.sequence_order,
            [{"source"}, {"resistor"}],
        )

    def test_start_csv_stream(self):
        my_coordinator = Coordinator()
        my_coordinator.start(
            conf_path=os.path.join("tests", "data", "config_with_csv.json")
        )
        self.assertEqual(
            my_coordinator.graph_engine.sequence_order,
            [{"source"}, {"resistor"}],
        )

    def test_do_step(self):
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        my_coordinator.do_step(step_size=0.05)

    def test_run_simulation(self):
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        my_coordinator.run_simulation(step_size=10, end_time=100)

    def test_get_results(self):
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        my_coordinator.run_simulation(step_size=10, end_time=100)
        results_df = my_coordinator.get_results()
        self.assertEqual(results_df, self.test_get_results_results)

    def test_save_results_csv(self):
        pass

    def test_get_results_no_run(self):
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        results_df = my_coordinator.get_results()
        self.assertEqual(results_df, {})

    def test_calls_no_start(self):
        my_coordinator = Coordinator()

        with self.assertRaises(RuntimeError):
            my_coordinator.get_results()

        with self.assertRaises(RuntimeError):
            my_coordinator.do_step(step_size=0.05)

        with self.assertRaises(RuntimeError):
            my_coordinator.run_simulation(step_size=10, end_time=100)

    def test_dict_tuple_to_dict_of_dict(self):
        my_coordinator = Coordinator()
        my_dict = {
            ("source", "V"): 1.0,
            ("resistor", "I"): 2.0,
        }
        my_dict_of_dict = {"source": {"V": [1.0]}, "resistor": {"I": [2.0]}}
        print(my_coordinator._dict_tuple_to_dict_of_dict(my_dict))
        self.assertEqual(
            my_coordinator._dict_tuple_to_dict_of_dict(my_dict), my_dict_of_dict
        )

    def test_get_variables(self):
        """Assert that the variable names and values are correct."""
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))

        # Assert that the variable names are correct
        var_names = my_coordinator.get_variable_names()
        expected_var_names = [
            ("source", "amplitude"),
            ("source", "frequency"),
            ("source", "phase"),
            ("source", "V"),
            ("resistor", "I"),
            ("resistor", "V"),
            ("resistor", "R"),
        ]
        assert var_names == expected_var_names

        # Assert that the variable value is correct (single variable)
        assert my_coordinator.get_variable(("source", "amplitude")) == [20.0]

        # Assert that the variable values are correct (multiple variables)
        var_values = my_coordinator.get_variables(
            [("resistor", "R"), ("source", "frequency")]
        )
        expected_values = {("resistor", "R"): [0.5], ("source", "frequency"): [1.0]}
        assert var_values == expected_values

    def test_get_causality(self):
        """Assert that the causality of variable is correct."""
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))

        # Assert that the causality of variables is correct
        var_names = my_coordinator.get_variable_names()
        causalities = [my_coordinator.get_causality(name) for name in var_names]
        p, o, i = ("parameter", "output", "input")
        expected_causalities = [p, p, p, o, o, i, p]
        assert causalities == expected_causalities

    def test_get_variable_type(self):
        """Assert that the variable type is correct."""
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))

        # Assert that the causality of variables is correct
        var_names = my_coordinator.get_variable_names()
        var_types = [my_coordinator.get_variable_type(name) for name in var_names]

        print(var_types)
        expected_var_types = ["Real"] * 7
        assert var_types == expected_var_types

    def test_save_results(self):
        """Assert that the results are saved correctly to a CSV file."""
        my_coordinator = Coordinator()
        my_coordinator.start(conf_path=os.path.join("tests", "data", "config.json"))
        my_coordinator.run_simulation(step_size=10, end_time=100)

        with tempfile.TemporaryDirectory() as tmpdirname:
            file_path = os.path.join(tmpdirname, "test.csv")
            my_coordinator.save_results(file_path)

            assert os.path.exists(file_path)

            with open(file_path, "r") as f:
                content = f.readlines()

        assert len(content) == 11
        assert content[0] == "time,resistor.I,source.V\n"
        assert content[1] == "0.0,0.0,0.0\n"
        assert content[-1] == "90.0,-3.1331150677801413e-13,-1.5665575338900706e-13\n"
