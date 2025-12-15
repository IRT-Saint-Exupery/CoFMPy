import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from cofmupy.utils.proxy import (
    FmuProxy,
    Variable,
    FmiCausality,
    FmiVariability,
    import_module_from_path,
    find_proxy_subclass,
    load_proxy_class_from_file,
)


class TestFmuProxy:
    def test_register_variable(self):
        proxy = FmuProxy()
        var = Variable(name="test_var", causality=FmiCausality.input, start=42)
        proxy.register_variable(var)

        assert len(proxy.variables()) == 1
        assert proxy.variables()[0].name == "test_var"
        assert proxy.test_var == 42

    def test_get_fmu_state(self):
        proxy = FmuProxy()
        var1 = Variable(name="var1", causality=FmiCausality.input, start=10)
        var2 = Variable(name="var2", causality=FmiCausality.output, start=20)
        proxy.register_variable(var1)
        proxy.register_variable(var2)

        state = proxy.getFMUstate()
        assert state == {"var1": 10, "var2": 20}

    def test_set_fmu_state(self):
        proxy = FmuProxy()
        var1 = Variable(name="var1", causality=FmiCausality.input, start=10)
        var2 = Variable(name="var2", causality=FmiCausality.output, start=20)
        proxy.register_variable(var1)
        proxy.register_variable(var2)

        proxy.setFMUstate({"var1": 100, "var2": 200})
        assert proxy.var1 == 100
        assert proxy.var2 == 200

    def test_set_fmu_state_invalid_variable(self):
        proxy = FmuProxy()
        with pytest.raises(
            AttributeError, match="Variable 'invalid_var' not found in the FMU."
        ):
            proxy.setFMUstate({"invalid_var": 123})

    def test_reset(self):
        proxy = FmuProxy()
        var = Variable(name="test_var", causality=FmiCausality.input, start=42)
        proxy.register_variable(var)

        proxy.test_var = 100
        proxy.reset()
        assert proxy.test_var == 42

    def test_do_step_not_implemented(self):
        proxy = FmuProxy()
        with pytest.raises(NotImplementedError):
            proxy.do_step(0.0, 1.0)


class TestUtilityFunctions:
    def test_import_module_from_path_invalid_path(self):
        with pytest.raises(FileNotFoundError, match="No such file: invalid_path.py"):
            import_module_from_path("invalid_path.py")

    def test_find_proxy_subclass_no_subclasses(self):
        @dataclass
        class DummyModule:
            __name__ = "test_proxy"

        module = DummyModule()
        module.SomeClass = object

        with pytest.raises(
            LookupError, match="No subclasses of FmuProxy found in module test_proxy"
        ):
            find_proxy_subclass(module, FmuProxy)

    def test_find_proxy_subclass_multiple_subclasses(self):
        @dataclass
        class DummyModule:
            __name__ = "test_proxy"

        class Subclass1(FmuProxy):
            pass

        class Subclass2(FmuProxy):
            pass

        module = DummyModule()
        module.Subclass1 = Subclass1
        module.Subclass2 = Subclass2

        with pytest.raises(LookupError):
            find_proxy_subclass(module, FmuProxy)

    def test_find_proxy_subclass_specific_class(self):
        @dataclass
        class DummyModule:
            __name__ = "test_proxy"

        class Subclass1(FmuProxy):
            pass

        class Subclass2(FmuProxy):
            pass

        module = DummyModule()
        module.Subclass1 = Subclass1
        module.Subclass2 = Subclass2

        result = find_proxy_subclass(module, FmuProxy, class_name="Subclass1")
        assert result == Subclass1

    def test_load_proxy_class_from_file_invalid_path(self):
        with pytest.raises(FileNotFoundError, match="No such file: invalid_path.py"):
            load_proxy_class_from_file("invalid_path.py")
