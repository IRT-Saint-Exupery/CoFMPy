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
Utility functions managing interpolation/extrapolation for
Co-simulation FMU Python toolbox.
"""

import logging
from typing import Iterable
import numpy as np
from scipy.interpolate import interp1d, make_interp_spline
import warnings

logger = logging.getLogger(__name__)


class Interpolator:
    """Interpolation class that abstracts the underlying library.
    Supports a variety of methods but can be enriched by registering
    new ones.
    Out-of-range (extrapolation) support depends on each registered method:
    as provided: numpy's interp and scipy's interp1d propagate the first xp value
    to the left while scipy's make_interp_spline computes spline at both boundaries.

    Raises:
        ValueError: if empty input arrays.
        ValueError: when mismatched lengths.
        ValueError: when unregistered method encountered.

    Returns:
        np.array: interpolated values
    """

    _registry = {}
    _min_points = {}

    def __init__(self, method: str = "previous", **kwargs: dict):
        """Initialize class with interpolation method and kwargs for registered
        interpolation methods.

        Args:
            method (str, optional): Interpolation method. Defaults to "previous".
        """
        self.method = method
        self.kwargs = kwargs
        self._validate_method()
        logger.info(f"Interpolator initialized with method: {self.method}")

    def _validate_inputs(self, xp: Iterable, yp: Iterable, x_new: Iterable):
        """Checks length consistency between arrays.
        Raises errors if inconsistent arrays are found.

        Args:
            xp (Iterable): x coordinates.
            yp (Iterable): y values.
            x_new (Iterable): x values to interpolate.

        Raises:
            ValueError: if empty input arrays.
            ValueError: when mismatched lengths.
        """
        if len(xp) == 0 or len(yp) == 0 or len(x_new) == 0:
            raise ValueError("Empty input arrays.")
        if len(xp) != len(yp):
            raise ValueError("Mismatched lengths for xp and yp.")

    def _validate_method(self):
        """Checks that method selected at init is registered.

        Raises:
            ValueError: when unregistered method encountered.
        """
        if self.method not in self._registry:
            raise ValueError(
                f"Unregistered method '{self.method}'. "
                f"Available: {set(self._registry)}"
            )
        if self.method not in ("linear", "previous"):
            warnings.warn(
                f"Method '{self.method}' is in beta version. "
                f"We recommend using 'linear' or 'previous'"
            )

    def _adjust_method(self, n_points: int):
        """Checks that selected method is adapted to array length.
        If not, another registered method is selected. This selection is
        done using sorted 'min_points' register argument.

        Args:
            n_points (int): length of value arrays.
        """
        for name, min_len in sorted(self._min_points.items(), key=lambda x: x[1]):
            if self.method == name and n_points < min_len:
                for fallback, required in sorted(
                    self._min_points.items(), key=lambda x: x[1]
                ):
                    if n_points >= required:
                        self.method = fallback
                        break

    @classmethod
    def register(cls, name: str, min_points: int):
        """Class method to register interpolation methods.

        Args:
            name (str): method name
            min_points (int, optional): minimum data points required.

        Registers:
            cls._registry (dict): {method_name: function}
            cls._min_points (dict): {method_name: min_data_len_required}

        Returns:
            decorator (callable): decorator to register methods.
        """

        def decorator(func):
            cls._registry[name] = func
            cls._min_points[name] = min_points
            return func

        return decorator

    def __call__(self, xp: Iterable, yp: Iterable, x_new: Iterable):
        """The Interpolator class is used as a callable after initialization.

        Args:
            xp (Iterable): x coordinates of data points.
            yp (Iterable): y data values.
            x_new (Iterable): x coordinates of points to interpolate.

        Returns:
            _type_: _description_
        """
        xp, yp, x_new = map(np.ravel, (xp, yp, x_new))
        self._validate_inputs(xp, yp, x_new)
        self._adjust_method(len(xp))
        return self._registry[self.method](xp, yp, x_new, self.method, **self.kwargs)


@Interpolator.register("linear", min_points=1)
def interp_linear(
    xp: Iterable, yp: Iterable, x_new: Iterable, _method: str = "", **kwargs: dict
):
    """Numpy wrapper for interp method. Default extrapolation behaviour is
    propagation of first and last values at left and right boundaries respectively.

    Args:
        xp (Iterable): x coordinates of data points.
        yp (Iterable): y data values.
        x_new (Iterable): x coordinates of points to interpolate.
        _method (str): does not apply here. used for registering consistency.
        kwargs (dict): keyword arguments for numpy.interp method.

    Returns:
        Iterable: interpolated values for x_new coordinates.
    """
    return np.interp(x_new, xp, yp, **kwargs)


@Interpolator.register("nearest", min_points=1)
@Interpolator.register("previous", min_points=1)
@Interpolator.register("quadratic", min_points=3)
@Interpolator.register("cubic", min_points=4)
def interp_scipy(
    xp: Iterable, yp: Iterable, x_new: Iterable, method: str, **kwargs: dict
):
    """Scipy wrapper for interp1d method.
    Default extrapolation behaviour is propagation of first and last values
    at left and right boundaries espectively.

    Args:
        xp (Iterable): x coordinates of data points.
        yp (Iterable): y data values.
        x_new (Iterable): x coordinates of points to interpolate.
        method (str): method to use as 'kind' argument in scipy's interp1d.
        kwargs (dict): keyword arguments for inner method.

    Returns:
        Iterable: interpolated values for x_new coordinates.
    """
    fun = interp1d(
        xp, yp, kind=method, bounds_error=False, fill_value=(yp[0], yp[-1]), **kwargs
    )
    return fun(x_new)


@Interpolator.register("spline", min_points=4)
def interp_spline(
    xp: Iterable, yp: Iterable, x_new: Iterable, _method: str = "", **kwargs: dict
):
    """_summary_

    Args:
        xp (Iterable): x coordinates of data points.
        yp (Iterable): y data values.
        x_new (Iterable): x coordinates of points to interpolate.
        _method (str): does not apply here. used for registering consistency.
        kwargs (dict): keyword arguments for scipy's make_interp_spline method.

    Returns:
        Iterable: interpolated values for x_new coordinates.
    """
    if len(xp) < 4:
        return np.interp(x_new, xp, yp)
    spline = make_interp_spline(xp, yp, **kwargs)
    return spline(x_new)
