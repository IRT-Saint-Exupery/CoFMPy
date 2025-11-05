# KafkaHandlerConfig

`KafkaHandlerConfig` is a **dataclass** used to configure Kafka connections for data handlers. It provides default values and validates configuration parameters automatically.

---

## 1. Initialization

You can create an instance by passing the required parameters:

```python
from your_module import KafkaHandlerConfig

config = KafkaHandlerConfig(
    topic="my_topic",
    server_url="localhost",
    port="9092",
    group_id="my_group",
    variable="temperature"
)
```

### Optional Parameters

* `timeout` (float, default `0.1`): Maximum wait time for Kafka operations (seconds). Must be non-negative.
* `interpolation` (str, default `"previous"`): Method to interpolate missing data. Must be one of the registered methods in `Interpolator`.
* `auto_offset_reset` (str, default `"earliest"`): Kafka consumer offset reset strategy. Options: `"earliest"`, `"latest"`, `"none"`.
* `enable_auto_commit` (bool, default `True`): Whether Kafka consumer auto-commits offsets.

### Validation

* `port` must be numeric.
* `timeout` must be non-negative.
* `auto_offset_reset` must be a valid value (`earliest`, `latest`, `none`).
* `interpolation` must be a valid method registered in `Interpolator`.

---

## 2. Creating from a dictionary

You can build a configuration from a dictionary (e.g., loaded from `config.json`) using `from_dict`:

```python
config_dict = {
    "uri": "localhost:9092",
    "topic": "my_topic",
    "variable": "temperature",
    "group_id": "my_group",
    "timeout": 0.5,
    "interpolation": "linear",
    "auto_offset_reset": "latest",
    "enable_auto_commit": False
}

config = KafkaHandlerConfig.from_dict(config_dict)
```

### Notes

* The `uri` field must be in the form `"server_url:port"`.
* Required dictionary keys: `"uri"`, `"topic"`, `"variable"`, `"group_id"`. Missing keys will raise a `KeyError`.
* Optional keys override the default values.

---

## 3. Usage

Once created, `KafkaHandlerConfig` instances store all necessary Kafka connection parameters:

```python
print(config.topic)           # "my_topic"
print(config.server_url)      # "localhost"
print(config.port)            # "9092"
print(config.interpolation)   # "linear"
```

* This object is typically passed to `KafkaDataStreamHandler` classes that manage consumption or production of data streams.

---

## 4. Logging and Error Handling

* Missing required dictionary keys are logged with `logger.error`.
* Invalid values for `port`, `timeout`, `auto_offset_reset`, or `interpolation` raise `ValueError` during initialization.

