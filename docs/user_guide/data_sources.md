# Managing data sources

External data can be useful to control variable parameters, to use as input from an
other system simulation or just to get from measurements from a physical twin.
CoFMPy provides multiple data source handlers detailed below.

Whatever the data source, the connection between the data source and the target variable
of the simulation is defined in the JSON configuration file as a connection:

```json
"connections": [
    {
        "source": {...},
        "target": {"id": "fmu_target", "variable": "my_variable", "unit": "my_unit"}
    },
    {
        ...
    }
]
```

## Single values, the simplest approach

If your variable is fixed or only changes a few times, this is the simplest way to
define the values. This is done directly in the JSON configuration file. The expected
format is a dictionary with times and values. For example `{"0": 1.0, "0.5": 2.8}`
corresponds to a variable that takes value 1.0 at the beginning of the simulation (t=0)
and have a single change at t=0.5 with the value 2.8. You can have either zero changes
(i.e. a fixed value for the whole simulation) or any changes you want.

The JSON configuration file must follow the syntax below:

```json
{
    "source": {
        "type": "local",
        "values": {"0": 0, "0.1": 12.2, "0.5": 8.6},
        "unit": "A"
    },
    "target": {"id": "FMU2", "variable": "Iload_in", "unit": "A"}
}
```

In case the variable has many changes, we suggest to use the second method, a CSV file.

## A CSV file

Data can be read directly from a CSV file. It must contain a first column with the time
instants, and other following columns with the values for one or several variables. A
file must start with a header containing the names of the columns: `t` for the first
column and the variable names for others, e.g. `t,R,V_out,Iload`.

Here is an example of data source CSV file:

```csv
t,R,V_out,Iload
0,100,5,0
0.1,100,5,0.8
0.5,100,10,0.8
0.7,200,5,2.5
```

To connect CSV data to an FMU variable in CoFMPy, the connection is described in the
JSON configuration file as follows:

```json
{
    "source": {
        "type": "csv",
        "path": "path/to/the/file.csv",
        "variable": "R",
        "interpolation": "previous",
        "unit": "Ohm"
    },
    "target": {"id": "resistor", "variable": "R", "unit": "Ohm"}
}
```

Note that a parameter can be defined when configuring the CSV source handler:

- `interpolation`: specifies the type of interpolation used when the system needs a
  value between two time points in the CSV file. It can be set to `previous`, which
  returns the previous value, or `linear`, which calculates a linearly interpolated
  value between the previous and next points. For example in the CSV file above, if
  `R` must be retrieved at t=0.65, if `interpolation="previous"` the data handler will
  return 100, being the previous value at t=0.5. If `interpolation="linear"` the data
  handler will return 175, being the linear interpolation between t=0.5 (R=100) and
  t=0.7 (R=200).

## A Kafka stream

The last data source proposed in CoFMPy is a Kafka broker. Data is retrieved from a
Kafka topic in a specific format: a message must contain the time instants and their
corresponding values. For example, a message with three values must be formatted as a
list of tuples:

```json
[
    (0, 100),
    (0.1, 200),
    (1.3, 52)
]
```

TODO: a topic per variable? Or a common topic and variables are received in the message?

To connect the Kafka topic to a FMU variable, the connection is described in the JSON
configuration file as follows:

```json
{
    "source": {
        "type": "kafka",
        "uri": "localhost:5000",
        "group_id": "my_group",
        "topic": "V_in",
        "variable": "V_in",
        "unit": "V"
    },
    "target": {"id": "voltage_source", "variable": "V_in", "unit": "V"}
}
```

Some parameters of the Kafka stream must be set:

- `uri`: the address of the Kafka server (with port information)
- `group_id`: the consumer group id
- `topic`: the topic to listen to

## Custom data sources

For advanced users, it is possible to create your own custom data stream handler that
feeds FMUs with external data. See page
[Create your own data stream handler](advanced/custom_stream_handler.md).
