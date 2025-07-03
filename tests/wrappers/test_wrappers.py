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
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
from conftest import (
    do_step,
    fmu_2_path,
    fmu_3_path,
    factory_class,
    description_class,
    float_precision,
    description_keys,
    nb_steps,
)


def test_fmi_version_not_recognized():
    # Mock the read_model_description function to return an unexpected FMI version
    with patch("cofmpy.wrappers.read_model_description") as mock_read_model:
        mock_description = MagicMock()
        mock_description.fmiVersion = "1.0"  # Unrecognized FMI version
        mock_read_model.return_value = mock_description

        with pytest.raises(ValueError, match="FMI version not recognized"):
            factory = factory_class("fake_path.fmu")
            factory()  # Calling the instance should raise the ValueError


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_factory_attributes(wrapper_params):
    (factory, fmu, var_dict, version, handler, slave, default_step) = (
        wrapper_params["factory"],
        wrapper_params["fmu"],
        wrapper_params["variables"],
        wrapper_params["version"],
        wrapper_params["handler"],
        wrapper_params["slave"],
        wrapper_params["default_step"],
    )

    # Factory object
    assert isinstance(factory, factory_class)
    assert isinstance(factory.path, str)
    assert isinstance(factory.description, description_class)
    assert "fmiVersion" in str(factory.description)
    assert factory.description.fmiVersion == version
    assert all(k in description_keys for k in factory.description.__dict__.keys())

    # FMU description as provided by factory
    assert isinstance(fmu, handler)
    assert isinstance(fmu.description, description_class)
    assert all(k in description_keys for k in fmu.description.__dict__.keys())
    assert "fmiVersion" in str(fmu.description)
    assert fmu.description.fmiVersion == version

    # FMU handler as provided by factory
    assert isinstance(fmu.fmu, slave)
    assert fmu.default_step_size == default_step
    assert isinstance(fmu.var_name2attr, dict)
    assert all(v in fmu.var_name2attr for v in sum(var_dict.values(), []))
    assert fmu.output_var_names == var_dict["out"]


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_variable_names(wrapper_params):
    fmu = wrapper_params["fmu"]
    expected_var_names = wrapper_params["expected_get_var"].keys()

    res = fmu.get_variable_names()
    assert sorted(res) == sorted(expected_var_names)


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_input_names(wrapper_params):
    var_dict, fmu = wrapper_params["variables"], wrapper_params["fmu"]
    assert fmu.get_input_names() == var_dict["in"]


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_output_names(wrapper_params):
    var_dict, fmu = wrapper_params["variables"], wrapper_params["fmu"]
    assert fmu.get_output_names() == var_dict["out"]


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_cancel_step(wrapper_params):
    fmu, exception, err_msg = (
        wrapper_params["fmu"],
        wrapper_params["exception"],
        wrapper_params["err_msg_cancel"],
    )

    with pytest.raises(exception) as exc_info:
        fmu.cancel_step()

    assert err_msg in str(exc_info.value)


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_state(wrapper_params):
    fmu, version, err_msg = (
        wrapper_params["fmu"],
        wrapper_params["version"],
        wrapper_params["err_msg_get"],
    )

    if version == "2.0":
        state = fmu.get_state()
        assert state is not None

    if version == "3.0":
        with pytest.raises(AttributeError) as exc_info:
            fmu.get_state()
        assert err_msg in str(exc_info.value)


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_set_state(wrapper_params):
    fmu, version, err_msg = (
        wrapper_params["fmu"],
        wrapper_params["version"],
        wrapper_params["err_msg_set_state"],
    )

    if version == "2.0":
        state = fmu.get_state()
        ret = fmu.set_state(state)
        assert ret is None
    if version == "3.0":
        with pytest.raises(AttributeError) as exc_info:
            fmu.set_state(None)
        assert err_msg in str(exc_info.value)


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_variables(wrapper_params):
    """Test the get_variables method of the FMU wrapper."""
    fmu, var_dict, expected_res = (
        wrapper_params["fmu"],
        wrapper_params["variables"],
        wrapper_params["expected_get_var"],
    )

    # Assert get_variable() with a single variable
    for vars in var_dict.values():
        for var in vars:
            res = fmu.get_variable(var)
            assert res == expected_res[var]

    # Assert get_variables() with a list of variables
    res = fmu.get_variables([v for var in var_dict.values() for v in var])
    assert res == expected_res


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_causality(wrapper_params):
    """Assert the get_causality() method of the FMU wrapper."""
    fmu, expected_res = wrapper_params["fmu"], wrapper_params["expected_get_causality"]

    var_names = fmu.get_variable_names()
    res = [fmu.get_causality(name) for name in var_names]
    assert res == expected_res


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_get_variable_type(wrapper_params):
    """Assert the get_variable_type() method of the FMU wrapper."""
    fmu, expected_res = wrapper_params["fmu"], wrapper_params["expected_var_types"]

    var_names = fmu.get_variable_names()
    res = [fmu.get_variable_type(name) for name in var_names]
    assert res == expected_res


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_set_variables(wrapper_params):
    fmu, version, var_dict, err_msg = (
        wrapper_params["fmu"],
        wrapper_params["version"],
        wrapper_params["variables"],
        wrapper_params["err_msg_set_var"],
    )

    res = fmu.set_variables({var_dict["out"][0]: [1.0]})
    assert res is None

    if version == "3.0":
        with pytest.raises(ValueError, match=err_msg):
            fmu.set_variables({var_dict["out"][0]: ["Not a float"]})


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_reset(wrapper_params):
    fmu, version = wrapper_params["fmu"], wrapper_params["version"]

    if version == "2.0":
        assert fmu.reset() is None
    if version == "3.0":
        for k, v in {"h": [1.0], "v": [0.0]}.items():
            fmu._set_variable(k, v)
        assert fmu.reset() is None


@pytest.mark.parametrize("wrapper_params", [fmu_2_path, fmu_3_path], indirect=True)
def test_step(wrapper_params):

    from conftest import current_time

    fmu, version, step_size, input_dict, expected_results = (
        wrapper_params["fmu"],
        wrapper_params["version"],
        wrapper_params["step_size"],
        wrapper_params["input_dict"],
        wrapper_params["expected_results"],
    )

    if version == "2.0":
        out_dict_1, current_time, input_dict = do_step(
            fmu, nb_steps, current_time, step_size, input_dict
        )

        fmu.fmu.setString([fmu.var_name2attr["string_var"].valueReference], ["reverse"])

        out_dict_2, current_time, input_dict = do_step(
            fmu, nb_steps, current_time, step_size, input_dict
        )

        assert out_dict_1["output_real"][0] == expected_results[0]
        assert out_dict_2["output_real"][0] == expected_results[1]

    if version == "3.0":
        for k, v in input_dict.items():
            fmu._set_variable(k, v)
        fmu.reset()

        out, _, _ = do_step(fmu, nb_steps, current_time, step_size, {})

        outputs = [np.round(v[0], float_precision) for v in out.values()]

        assert outputs == expected_results
