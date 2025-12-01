# Managing data sources

External data can be useful to control variable parameters, to use as input from an
other system simulation or just to get from measurements from a physical twin.
CoFMPy provides multiple data source handlers detailed below.

Whatever the data source, the connection between the data source and the target variable
of the simulation is defined in the JSON configuration file as a connection:

- a `source` field defining the data handler configuration (see below the supported data
  handlers).
- a `target` field corresponding to the FMU variable connected to the source.

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

## Single values, the simplest approach (`literal` data handler)

If your variable is fixed or only changes a few times, this is the simplest way to
define the values. This is done directly in the JSON configuration file. The expected
format is a dictionary with times and values. For example `{"0": 1.0, "0.5": 2.8}`
corresponds to a variable that takes value 1.0 at the beginning of the simulation (t=0)
and have a single change at t=0.5 with the value 2.8. You can have either zero changes
(i.e. a fixed value for the whole simulation) or any changes you want. As JSON only
accepts string keys, remember that time instants must be with quote (e.g. `"0.5"`).

The JSON configuration file must follow the syntax below:

```json
{
    "source": {
        "type": "literal",
        "values": {"0": 0, "0.1": 12.2, "0.5": 8.6},
        "unit": "A"
    },
    "target": {"id": "FMU2", "variable": "I_load", "unit": "A"}
}
```

In case the variable has many changes, we suggest to use the second method, a CSV file.

## A CSV file

Data can be read directly from a CSV file.  The file must start with a header containing
the names of the columns: a column titled `t` containing the time instants, and the
other columns titled with variable names. For example, the CSV header could be
`t,R,V_out,Iload`.

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
        "unit": "Ohm"
    },
    "target": {"id": "resistor", "variable": "R", "unit": "Ohm"}
}
```

## A Kafka stream

The last data source proposed in CoFMPy is a Kafka broker. Data is retrieved from a
Kafka topic in a specific format: a message must contain the time instants and their
corresponding values as a dictionary:

```json
{"t": 0, "R": 100},
{"t": 0.1, "R": 200}
```

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

For a more detailed example of Kafka configuration, please read [Kafka Handler
Configuration](advanced/kafka_configuration.md). For a deeper understanding of the Kafka
Thread Manager, see [this page](advanced/kafka_thread_manager.md).

## Interpolation between time instants (optional parameter)

Whatever the data source, an optional parameter `interpolation` can be added to the
configuration. This parameter specifies the type of interpolation used when the system
needs a value between two time points. It can be set to `previous`, which returns the
previous value (default value), or `linear`, which calculates a linearly interpolated
value between the previous and next points. For example for a value of 100 at t=0.5 and
200 at t=0.7, if we want to retrieve the value at t=0.65:

- if `interpolation="previous"` the data handler will return 100, being the previous
  value at t=0.5.
- if `interpolation="linear"` the data handler will return 175, being the linear
  interpolation between t=0.5 (R=100) and t=0.7 (R=200).

## Custom data sources

For advanced users, it is possible to create your own custom data stream handler that
feeds FMUs with external data. See page [Data Stream Handler
Module](advanced/stream_handler_module.md).
