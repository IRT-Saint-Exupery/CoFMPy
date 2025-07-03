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
import unittest
import numpy as np

from cofmpy.utils import Interpolator


class TestInterpolator(unittest.TestCase):

    def setUp(self):
        """Set up test data."""
        self.methods = ["linear", "cubic", "quadratic", "previous", "nearest", "spline"]
        self.data_types = ["array", "list"]
        self.x = np.array([0, 1, 2, 3, 4])
        self.y = np.array([0, 2, 1, 3, 7])
        self.x_new = np.linspace(0, 4, 10)

        # Expected results
        self.y_expected_results = {
            "linear": [
                0.0,
                0.88889,
                1.77778,
                1.66667,
                1.22222,
                1.44444,
                2.33333,
                3.44444,
                5.22222,
                7.0,
            ],
            "cubic": [
                0.0,
                1.75537,
                2.06767,
                1.61728,
                1.08459,
                1.13077,
                1.97531,
                3.39598,
                5.15135,
                7.0,
            ],
            "quadratic": [
                0.0,
                1.38977,
                1.97813,
                1.76508,
                1.0769,
                1.14039,
                2.03492,
                3.36261,
                5.01764,
                7.0,
            ],
            "previous": [0.0, 0.0, 0.0, 2.0, 2.0, 1.0, 1.0, 3.0, 3.0, 7.0],
            "nearest": [0.0, 0.0, 2.0, 2.0, 1.0, 1.0, 3.0, 3.0, 7.0, 7.0],
            "spline": [
                0.0,
                1.75537,
                2.06767,
                1.61728,
                1.08459,
                1.13077,
                1.97531,
                3.39598,
                5.15135,
                7.0,
            ],
        }

        # Out-of-bounds x_new points
        self.oob_pts = (np.array([-1]), np.array([10]))

        # Expected results for oob
        self.oob_expected = {
            "linear": [0, 7],
            "cubic": [0, 7],
            "quadratic": [0, 7],
            "previous": [0, 7],
            "nearest": [0, 7],
            "spline": [-12.75, -81],
        }

        # Non conform test cases
        self.non_conform = [([], [1], [0.5]), ([1], [], [0.5]), ([1], [1], [])]

    def _transform_type(self, data_type):
        """Convert data to different formats."""
        if data_type == "array":
            return self.x, self.y, self.x_new
        if data_type == "list":
            return self.x.tolist(), self.y.tolist(), self.x_new.tolist()

    def _transform_data_types(test_func):
        """Decorator to transform test data types."""

        def wrapper(self):
            for data_type in self.data_types:
                xp, yp, x_new = self._transform_type(data_type)
                test_func(self, xp, yp, x_new)

        return wrapper

    @_transform_data_types
    def test_invalid_method_and_type(self, xp, yp, x_new):
        """Test that an invalid interpolation method raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Unregistered method 'invalid'.*"):
            Interpolator(method="invalid")(xp, yp, x_new)

    @_transform_data_types
    def test_non_conform_arrays(self, xp, yp, x_new):
        """Ensure empty input arrays raise ValueError."""
        for tc in self.non_conform:
            with self.assertRaisesRegex(ValueError, "Empty input arrays."):
                Interpolator(method="linear")(*tc)
        with self.assertRaisesRegex(ValueError, "Mismatched lengths for xp and yp."):
            Interpolator(method="linear")([1], [1, 2], [0.5])

    @_transform_data_types
    def test_valid_methods(self, xp, yp, x_new):
        """Test all supported interpolation methods."""
        for method in self.methods:
            y_interp = Interpolator(method=method)(xp, yp, x_new)

            self.assertEqual(y_interp.shape, self.x_new.shape)
            self.assertTrue(np.all(np.isfinite(y_interp)))
            np.testing.assert_allclose(
                y_interp, self.y_expected_results[method], rtol=1e-5
            )

    def test_single_data_point(self):
        """Test interpolation with a single data point."""
        x_single, y_single, x_new, y_expected = (np.array([2]) for _ in range(4))
        for method in self.methods:
            y_interp = Interpolator(method=method)(x_single, y_single, x_new)
            np.testing.assert_allclose(y_interp, y_expected)

    @_transform_data_types
    def test_out_of_bounds_values(self, xp, yp, x_new):
        """Test behavior with values outside the provided x range."""
        for method in self.methods:
            y_interp = Interpolator(method=method)(xp, yp, self.oob_pts)
            np.testing.assert_allclose(y_interp, self.oob_expected[method])


if __name__ == "__main__":
    unittest.main()
