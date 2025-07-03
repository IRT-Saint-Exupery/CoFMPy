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
Utility functions for solving Co-simulation routines.
"""

import numpy as np
from scipy.optimize import fsolve, root


class FixedPointInitializer:
    """
    A modular solver for fixed-point initialization of coupled FMUs.
    Ensures identical results to the original _fixed_point_init function.
    """

    def __init__(self, master, solver, time_step, **kwargs):
        """
        Initialize the FixedPointSolver.

        Args:
            master: The master simulation manager handling FMUs.
            solver (callable): The solver function.
            time_step (float): Time step for the fixed-point iterations.
            kwargs: Additional keyword arguments for the solver.
                Depends on the solver used, e.g. for scipy.optimize.fsolve: {"xtol": 1e-6}.
        """
        self.master = master
        self.solver = solver
        self.time_step = time_step
        self.kwargs = kwargs

        # Compute updatable inputs and mappings
        self.updatable_inputs = self._get_updatable_inputs()
        self.input_fmuid_varname2idx = self._create_input_index_mapping()
        self.free_mask = self._create_free_mask()

    def get_config(self):
        """
        Get the configuration of the FixedPointSolver.

        Returns:

            dict: A structured dictionary representing the solver configuration.
        """

        return {
            "solver": self.solver,
            "time_step": self.time_step,
            "updatable_inputs": self.updatable_inputs,
        }

    def solve(self):
        """
        Solves the fixed-point problem to find a consistent initial state.

        Returns:
            dict: A structured dictionary representing the solved initial state.
        """
        # Step 1: Flatten input dictionary
        initial_flat_guess = self._flatten_dict(self.master.get_input_dict())

        # Step 2: Reset FMUs before solving
        self._reset_fmus()

        # Step 3: Solve the fixed-point equation
        solution_free = self._solve_fixed_point(initial_flat_guess)

        # Step 4: Reconstruct the full solution from the solver output
        full_solution = np.copy(initial_flat_guess)
        full_solution = np.where(self.free_mask, solution_free, full_solution)
        structured_solution = self._construct_from_flat(full_solution)

        print("✅ Fixed-point solution found:", structured_solution)
        return structured_solution

    # ============================ HELPER METHODS ============================

    def _get_updatable_inputs(self):
        """
        Identify which inputs can be modified (only inputs involved in connections
        between two FMUs).
        """
        inputs_in_fmu2fmu_connections = []
        for input_vars in self.master.connections.values():
            inputs_in_fmu2fmu_connections.extend(input_vars)
        return inputs_in_fmu2fmu_connections

    def _create_input_index_mapping(self):
        """Create a mapping from (fmu_id, var_name) to an index in the flattened input array."""
        return {
            (fmu_id, var_name): idx
            for idx, (fmu_id, var_name) in enumerate(
                (
                    (fmu_id, var_name)
                    for fmu_id in self.master.get_input_dict()
                    for var_name in self.master.get_input_dict()[fmu_id]
                )
            )
        }

    def _create_free_mask(self):
        """Create a mask to indicate which variables are free to change."""
        free_mask = np.zeros(len(self.input_fmuid_varname2idx), dtype=int)
        updatable_set = set(self.updatable_inputs)
        for key in updatable_set:
            if key in self.input_fmuid_varname2idx:
                free_mask[self.input_fmuid_varname2idx[key]] = 1
        return free_mask

    def _flatten_dict(self, input_dict):
        """Flatten a structured dictionary into a 1D array for the solver."""
        return np.concatenate(
            [
                np.array(list(inputs.values())).flatten()
                for inputs in input_dict.values()
            ]
        )

    def _construct_from_flat(self, flat_array):
        """Reconstruct a structured dictionary from the flattened input array."""
        structured_dict = {}
        for fmu_id, input_vars in self.master.get_input_dict().items():
            structured_dict[fmu_id] = {
                var_name: [flat_array[self.input_fmuid_varname2idx[(fmu_id, var_name)]]]
                for var_name in input_vars
            }
        return structured_dict

    def _reset_fmus(self):
        """Reset all FMUs before and after fixed-point iterations."""
        for fmu_handler in self.master.fmu_handlers.values():
            fmu_handler.reset()
        self.master.current_time = 0.0

    def _solve_fixed_point(self, initial_flat_guess):
        """Solve the fixed-point equation using the specified numerical solver."""

        def residual(x):
            """
            Compute the residual: g(x) = f(x) - x.
            The residual is calculated based on updated outputs versus the current guess.
            """
            # Reconstruct full vector by inserting updated free variables
            full_x_flat = np.copy(initial_flat_guess)
            full_x_flat = np.where(self.free_mask, x, full_x_flat)
            guess_dict = self._construct_from_flat(full_x_flat)

            # Perform a simulation step
            output_dict = self.master.do_step(
                self.time_step, guess_dict, record_outputs=False
            )

            # Compute residuals only for free variables
            residuals = np.zeros_like(x, dtype=np.float64)
            for fmu_id, output_vars in output_dict.items():
                for var_name, output_val in output_vars.items():
                    try:
                        input_fmu_id_vars = self.master.connections[(fmu_id, var_name)]
                        for input_fmu_id_var in input_fmu_id_vars:
                            input_index = self.input_fmuid_varname2idx[input_fmu_id_var]
                            if input_fmu_id_var in self.updatable_inputs:
                                residuals[input_index] = (
                                    output_val[0] - full_x_flat[input_index]
                                )
                    except KeyError:
                        pass  # Ignore missing connections
            self._reset_fmus()  # Reset FMUs after computation
            return np.array(residuals)

        # Solve using fsolve
        if self.solver == "fsolve":
            solution, infodict, ier, msg = fsolve(
                func=residual,
                x0=initial_flat_guess,
                full_output=True,
                **self.kwargs,
            )
            if ier != 1:  # ier == 1 means success
                raise RuntimeError(
                    "❌ Fixed-point initialization did not converge: " + msg
                )
            print(msg + f" ✅ After {infodict['nfev']} iterations, solution found:")
            return solution

        # Solve using root
        if self.solver == "root":
            result = root(
                fun=residual,
                x0=initial_flat_guess,
                method="broyden1",
                **self.kwargs,
            )
            if not result.success:
                raise RuntimeError(
                    "❌ Fixed-point initialization did not converge: " + result.message
                )
            return result.x

        raise ValueError("❌ Unsupported solver: " + str(self.solver))
