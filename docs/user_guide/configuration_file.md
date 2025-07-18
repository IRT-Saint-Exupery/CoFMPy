# Writing a JSON configuration file

This guide will help you write a JSON configuration file to define FMUs, their
properties, the connections between FMUs and connections with external data.

## Structure of the configuration file

The configuration file consists of three main sections:

1. FMUs (`fmus`): defines individual FMUs and their properties (id, path, step size,
  supplier, etc.)
2. Connections (`connections`): describes the connection graph.
3. Global settings: specifies global configuration options.

## 1. Defining FMUs

The `fmus` section contains the list of FMUs. Each FMU is represented by a dictionary
with the following attributes:

- `id`: a unique identifier for the FMU (e.g., "FMU1" or "rotor").
- `path`: the file path of the FMU (see below).
- `stepsize`: the step size for the FMU simulation (e.g., "0.3 sec").
- `name` (optional): a human-readable name for the FMU (e.g., "load").
- `initialization` (optional): key-value pairs to initialize variables in the FMU. An
  initialization value could be overridden if a connection is defined for this variable.
- `supplier` (optional): the supplier or creator of the FMU.

Here is an example of an FMU description:

```json
{
    "id": "load",
    "path": "load.fmu",
    "stepsize": "0.2 sec",
    "name": "variable load",
    "initialization": {"V_in": 800, "R": 2.5},
    "supplier": "My company"
}
```

### Paths to FMU files

Paths to FMU files can be specified as:

1. Relative paths. The configuration parser will search for files using `path` value,
by considering the following:
  * Files are placed at the same level than the configuration JSON file or in nested folders.
  * Each FMU file at the previously mentioned location has a unique name.

2. Absolute paths. In this case, the `path` field will remain untouched and the FMUs will
be loaded from the specified locations.

## 2. Defining Connections

The `connections` section is a list of connections. A connection links a source to a
target. The generic JSON structure for a connection is:

```json
{
    "source": {...},
    "target": {...}
}
```

Three types of connections can be defined in the JSON file:

- a connection between two FMUS
- a connection from a data source to an FMU
- a connection from an FMU to a data "sink"

Each connection type is described in the following subsections.

### Between two FMUs

A connection between two FMUs represents the interaction between the subsystems in
the co-simulation. The connection links the output variable of an FMU to the input
variable of another FMU. A source/target for an FMU is defined with:

- `id`: the FMU id as defined in the `fmus` section.
- `variable`: the variable name in the FMU
- `unit`: (optional) the unit of the variable

##### Example

For a connection from variable `I_out` of FMU `battery` to variable `Iload_in` of FMU
`load`, the JSON description is:

```json
{
    "source": {"id": "battery", "variable": "I1_out", "unit": "A"},
    "target": {"id": "load", "variable": "Iload_in"}
}
```

!!! note
    A connection source/target has a `type` which is `fmu` by default. It is possible
    to add this field to be more explicit in the JSON: `"type": "fmu"`.

### From a data source to an FMU

A connection from an external data source to an FMU is required when one input variable
of a FMU is controlled by external data. The data source will be used as input values
for the FMU. In CoFMPy, we provide multiple external data sources: from single values,
from a CSV file, or from a Kafka stream. You can also create your own data source (see
documentation).

The information required varies depending on the data source. For each type of source,
a field `type` is required. Note that for all types, the field `unit` is optional.

#### **From single values (literal)**

- `type`: `literal`
- `values`: a key-value dictionary <time,val> with the values of the variable at
  different timestamps, e.g. `{"0.1": 12.2, "0.5": 8.6}`. Note that keys in JSON must
  be strings, timestamps "0.1" and "0.5" above are then represented as strings.
- `interpolation`: (optional) interpolation method (see [interpolation reference](#interpolation-reference)). Defaults to `previous`.

##### Example

The variable `R` of a FMU `resistor` is defined as "literal".
The corresponding JSON description is:

```json
{
    "source": {
        "type": "literal",
        "values": {"0": 100, "12.5": 250},
        "interpolation": "linear"
    },
    "target": {"id": "resistor", "variable": "R", "unit": "Ohm"}
}
```

#### **From a CSV file**

- `type`: `csv`
- `path`: the path to the CSV file
- `variable`: the variable name to read in the CSV. It must correspond to the column
  header name.
- `interpolation`: (optional) interpolation method (see [interpolation reference](#interpolation-reference)). Defaults to `previous`.

If you want to know how CSV files must be formatted to be correctly read by CoFMPy,
refer to the section on [CSV data source](data_sources.md#a-csv-file).

##### Example

The variable `V` of FMU `battery` is controlled according to the values in the CSV file
`path/to/battery_data.csv` (column called `voltage`). The interpolation is set to
`previous`. The corresponding JSON connection is:

```json
{
    "source": {
        "type": "csv",
        "path": "path/to/battery_data.csv",
        "variable": "voltage",
        "unit": "V",
        "interpolation": "previous"
    },
    "target": {"id": "battery", "variable": "V", "unit": "V"}
}
```

#### **From a Kafka stream**

- `type`: `kafka`
- `uri`: the server URL (with port), e.g. `127.0.0.1:9092`
- `group_id`: the consumer group id.
- `topic`: the topic to listen to.
- `variable`: the variable name to read in the Kafka topic. It must correspond to the
  variable name used in the Kafka message.
- `interpolation`: (optional) interpolation method (see [interpolation reference](#interpolation-reference)). Defaults to `previous`.
- `timeout`: (optional) delay, in seconds, to wait (blocking) after reception of the first message before proceeding with the rest of the cosimulation. Defaults to `2`.


If you want to know how Kafka messages must be formatted to be correctly read by CoFMPy,
refer to the section on [Kafka data source](data_sources.md#a-kafka-stream).

##### Example

The variable `V` of FMU `battery` is controlled by the values from a Kafka server. A single message is formatted as follows: `{"t":, "":, "":, "":, }`. The corresponding JSON connection is:

```json
{
    "source": {
        "type": "kafka",
        "uri": "172.17.0.1:5000",
        "group_id": "my_group",
        "topic": "cofmpy_topic",
        "variable": "voltage",
        "interpolation": "linear",
        "timeout": 1,

    },
    "target": {"id": "battery", "variable": "V", "unit": "V"}
}
```

### From an FMU to a data sink

A connection from an FMU to a data "sink" represents a connection towards the "outside".
A sink can be a data storage system (e.g. a file or database system) or an outbound
data stream (e.g. a Kafka data stream). The JSON description is equivalent to the
previous cases.

By default, CoFMPy will save all output variables of the co-simulation in a single CSV
file for each simulation step. The location of this file is `storage/results.csv`.

#### To a CSV file

- `type`: `csv`
- `output_dir`: the directory where the CSV file will be created.
- `variable`: the name of the variable, used as the CSV filename and the header column
  name in the CSV file.
- `overwrite`: (optional) overwrite an existing file if `true`. Defaults to `true`.
- `unit`: (optional) the unit of the variable.

##### Example

```json
{
    "source": {"id": "FMU1", "variable": "V_out", "unit": "V"},
    "target": {
        "type": "csv",
        "id": "csv_out_V",
        "output_dir": "path/to/folder/",
        "variable": "FMU1.V",
        "overwrite": true
    }
}
```

#### To a Kafka stream

- `id`: an ID to name the connection
- `uri`: the Kafka server URL (with the port number)
- `variable`: the name of the variable, used to send messages on the Kafka topic.
- `group_id`: the consumer group id.
- `topic`: the topic to listen to.
- `unit`: (optional) the unit of the variable.

##### Example

A JSON example for Kafka data stream:

```json
{
    "source": {"id": "FMU2", "variable": "I_out", "unit": "A"},
    "target": {
        "type": "kafka",
        "id": "kafka_out_1",
        "uri": "172.17.0.1:5050",
        "variable": "FMU2.I",
        "config": {"group_id": "my_group", "topic": "FMU2.I"},
        "unit": "A"
    }
}
```

## 3. Global settings

Besides the description of the FMUs and the connections, the JSON configuration file
also specifies global settings used by CoFMPy.

- `loop_method`: specifies the algorithm for solving system loops (e.g., `jacobi`,
  `gauss-seidel`).
- `edge_sep`: defines the separator for connection naming. Default is ` -> `.
- `root`: specifies the root directory for relative paths.

## Tips for writing a configuration file

- Use unique IDs: ensure all FMUs and data sources have unique IDs.
- Verify paths: check that all path attributes are valid and accessible.
- Specify units: use consistent units across all variables to avoid mismatches.
- Test connections: verify connections are logical and complete.
- Validate JSON: Use a JSON validator to ensure the configuration file is error-free.

This guide should help users create and manage their JSON configuration files
effectively. A full JSON example is provided in the "Examples" section.

## Interpolation reference

Interpolation is used when the system
needs a value between two time points when data external to FMUs is used (literal, csv, kafka, etc.).

The interpolation uses `cofmpy.utils.Interpolator` class which supports a wide variety of interpolation methods. The currently tested methods are:
- `previous`, which returns the value at the previous time point (default value)
- `linear`, which calculates a linearly interpolated value between the previous and
  next points.

The other methods will log the following warning:
`Method '{method}' is in beta version. We recommend using 'linear' or 'previous'`

For more details, please refer to: `./notebooks/interpolator.ipynb`
