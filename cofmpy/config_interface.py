
from typing import Union
from typing import Dict
from dataclasses import dataclass

FMU_TYPE = "fmu"
CSV_TYPE = "csv"
LITERAL_TYPE = "literal"


class ConfigConnectionBase:
    type: str


class ConfigConnectionFmu(ConfigConnectionBase):
    id: str
    variable: str
    unit: str

    def __init__(
        self,
        id: str,
        variable: str,
        unit: str = "",
        type: str = FMU_TYPE,
        **kwargs
    ):
        self.type = type
        self.id = id
        self.variable = variable
        self.unit = unit

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        return {
            "type": self.type,
            "id": self.id,
            "variable": self.variable,
            "unit": self.unit
        }


class ConfigConnectionLocalStream(ConfigConnectionBase):
    values: Dict
    interpolation: str
    variable: str = ""

    def __init__(
        self,
        type: str,
        values: Dict,
        interpolation="previous",
        **kwargs
    ):
        self.type = type
        self.values = values
        self.interpolation = interpolation

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        return {
            "type": self.type,
            "values": self.values,
            "variable": self.variable,
            "interpolation": self.interpolation
        }


class ConfigConnectionCsvStream(ConfigConnectionBase):
    path: str
    variable: str = ""
    interpolation: str

    def __init__(
        self,
        type: str,
        path: str,
        variable: str,
        interpolation="previous",
        **kwargs
    ):
        self.type = type
        self.path = path
        self.variable = variable
        self.interpolation = interpolation

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        return {
            "type": self.type,
            "path": self.path,
            "variable": self.variable,
            "interpolation": self.interpolation
        }


class ConfigConnectionStorage(ConfigConnectionBase):
    id: str
    variable: str = ""
    alias: str

    def __init__(
        self,
        id: str,
        alias: str,
        type: str,
        **kwargs
    ):
        self.type = type
        self.id = id
        self.alias = alias

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        return {
            "type": self.type,
            "id": self.id,
            "variable": self.variable,
            "alias": self.alias
        }


class ConfigDataStorage:
    name: str
    type: str
    config: Dict

    def __init__(
        self,
        name: str,
        type: str,
        config: Dict,
        **kwargs
    ):
        self.name = name
        self.type = type
        self.config = config

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        return {
            "name": self.name,
            "type": self.type,
            "config": self.config
        }


class ConfigConnection:
    source: Union[ConfigConnectionFmu, ConfigConnectionLocalStream, ConfigConnectionCsvStream]
    target: list[Union[ConfigConnectionFmu, ConfigConnectionStorage]] = []

    def __init__(
        self,
        source: Dict,
        target: list[Dict],
        **kwargs
    ):
        if source["type"] == FMU_TYPE:
            self.source = ConfigConnectionFmu(**source)
        elif source["type"] == CSV_TYPE:
            self.source = ConfigConnectionCsvStream(**source)
        elif source["type"] == LITERAL_TYPE:
            self.source = ConfigConnectionLocalStream(**source)

        if not isinstance(target, list):
            # TODO : Manage error on config format
            print(f"target is not a list")
            target = [target]

        self.target = []
        for target_dict in target:
            if target_dict["type"] != FMU_TYPE:
                self.target.append(ConfigConnectionStorage(**target_dict))
            else:
                self.target.append(ConfigConnectionFmu(**target_dict))

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")


class ConfigFmu:
    id: str
    name: str
    path: str
    initialization: Dict = {}

    def __init__(
        self,
        id: str,
        path: str,
        name: str = "",
        initialization: dict = {},
        **kwargs
    ):
        self.id = id
        self.name = name
        if name == "":
            self.name = id
        self.path = path
        self.initialization = initialization

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        print('Path for fmu is '+self.path)
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "initialization": self.initialization
        }


class ConfigObject:
    root: str
    edge_sep: str
    cosim_method: str
    iterative: bool
    fmus: list[ConfigFmu] = []
    connections: list[ConfigConnection] = []
    data_storages: list[ConfigDataStorage] = []

    def __init__(
        self,
        fmus: list[ConfigFmu],
        connections: list[ConfigConnection],
        data_storages: list[ConfigDataStorage] = [],
        root: str = "",
        edge_sep: str = " -> ",
        cosim_method: str = "jacobi",
        iterative: bool = False,
        **kwargs
    ):
        self.fmus = [ConfigFmu(**fmu_dict) for fmu_dict in fmus]
        self.connections = [ConfigConnection(**connection_dict) for connection_dict in connections]
        self.data_storages = [ConfigDataStorage(**storage_dict) for storage_dict in data_storages]
        self.edge_sep = edge_sep
        self.cosim_method = cosim_method
        self.iterative = iterative
        self.root = root

        # Add warning for not used properties
        for arg in kwargs.keys():
            print(f"Unknown property is ignore : {arg}")

    def asdict(self):
        connections = []
        for connection in self.connections:
            for target in connection.target:
                connections.append(
                    {
                        "source": connection.source.asdict(),
                        "target": target.asdict()
                    }
                )
        return {
            "root": self.root,
            "edge_sep": self.edge_sep,
            "cosim_method": self.cosim_method,
            "iterative": self.iterative,
            "fmus": [fmu.asdict() for fmu in self.fmus],
            "connections": connections,
            "data_storages": [storage.asdict() for storage in self.data_storages]
        }