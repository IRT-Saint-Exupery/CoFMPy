# Data Stream Handler module

This section describes the architecture, usage, and available implementations of data stream handlers within CoFMPy.

---
## 1. Overview

The `data_stream_handler` module provides a unified interface for ingesting and interacting with live or recorded data streams, which serve as inputs to Digital Twin prototypes. It enables users to seamlessly switch between data sources (e.g., CSV files, Kafka topics, or local in-memory streams) through a consistent API. This abstraction layer allows developers to prototype and test Digital Twins without rewriting data ingestion logic.

### Core Concepts

* **Modularity & Extensibility:** All stream handlers inherit from `BaseDataStreamHandler`, which defines the standard interface and registration mechanism for new handlers.
* **Handler Factory:** Stream handler instances are dynamically instantiated using the `BaseDataStreamHandler.create_handler()` factory method, based on the configuration dictionary.
* **Grouped data streams:** Control over dynamic instantiation and variable assignment is provided by `BaseDataStreamHandler.is_equivalent_stream()` and `BaseDataStreamHandler.add_variable()` methods, respectively.
* **Alias Mapping:** A mechanism for mapping CoFMPy internal connections (as `(node, endpoint)` tuples) to external variables in the input data stream.
* **Data Interpolation:** Each handler supports time-based interpolation (e.g., step-wise or linear), using the shared `Interpolator` utility.

### Included Handlers

* **CSVDataStreamHandler** (`csv`): Reads data from a static CSV file.
* **KafkaDataStreamHandler** (`kafka`): Connects to a Kafka topic, consumes real-time messages in a separate thread and manages buffering.
* **LocalDataStreamHandler**: Provides a lightweight in-memory option for development, unit testing, or variable with very few variations in time.

Each handler needs to include (explained below):

* `get_data(t)`
* `is_equivalent_stream(config)`
* `add_variable(endpoint, alias)`

### Example Use

```python
config = {
    "type": "csv",
    "config": {
        "path": "data/simulation.csv",
        "interpolation": "linear"
    }
}

handler = BaseDataStreamHandler.create_handler(config)
handler.add_variable(("robot", "position"), "robot_pos")
data_at_t = handler.get_data(t=5.0)
```

This architecture enables rapid experimentation and stream interchangeability, making it ideal for fast prototyping of Digital Twin models.

---
## 2. BaseDataStreamHandler

The `BaseDataStreamHandler` provides the abstract common interface for all data stream handlers, in particular, it: 
* Defines a uniform API for time-based data retrieval (`get_data`)
* Enables extensibility through a registry and factory method
* Manages alias mappings between CoFMPy connections and stream variables
* Supports equivalence checks for grouping data streams in a single handler (`is_equivalent_stream`)

### Core Methods

* `get_data(t: float) -> pd.Series`
  Must be implemented by child classes to return the data at time `t`. Interpolation behavior is defined per handler instance.

* `add_variable(endpoint: tuple, stream_alias: str)`
  Updates the mapping between a COFMPy connection variable (as a `(node, endpoint)` tuple) and its name in the data stream.

* `is_equivalent_stream(config: dict) -> bool`
  Used to check if a new config would produce an equivalent stream handler instance (e.g., same CSV file path, same Kafka topic, etc.).

### Handler Registration and Factory

All subclasses must define a unique `type_name` class attribute. They are automatically registered via `register_handler` and can be instantiated using:

```python
handler = BaseDataStreamHandler.create_handler(config_dict)
```

The `config_dict` must follow this structure:

```python
{
    "type": "<type_name>",
    "config": { ... }  # handler-specific config
}
```

For integration with the rest of CoFMPy modules, new subclasses have to be **imported and registered** in the module's `__init__.py`.

### Alias Mapping

Handlers store connection mappings internally using a dictionary:

```python
alias_mapping: dict[tuple[str, str], str]
```

This mapping is used to translate CoFMPy internal references to stream-specific variable names during data retrieval.

---
## 3. Available Handlers

The following data stream handlers are included by default and can be selected using the `type` field in the configuration. Each handler implements the core interface defined in `BaseDataStreamHandler`, with behavior tailored to its data source.

### 3.1. CSVDataStreamHandler (`type: "csv"`)

Reads time-indexed data from a static CSV file.

#### Configuration

```python
{
    "type": "csv",
    "config": {
        "path": "path/to/file.csv",
        "interpolation": "previous"  # optional, defaults to "previous"
    }
}
```

#### Notes

* The entire CSV is loaded into memory at initialization.
* Time interpolation is handled using the configured method (e.g., "previous", "linear").
* Use `add_variable()` to map model endpoints to column names in the file.


### 3.2. LocalDataStreamHandler

Lightweight handler designed for manually provided in-memory data.

#### Use Cases

* Scenario implementation
* Fast iteration with known values
* Manual injection of sequence of parameters

#### Notes

* Values can be passed dynamically in the workflow.

### 3.3. KafkaDataStreamHandler (`type: "kafka"`)

The `KafkaDataStreamHandler` connects to a Kafka topic to receive **online data**. It uses background threading and fast buffering to ensure consistent access to interpolated time-series values, even under asynchronous message arrival.

This handler is suited for live Digital Twin deployments or fast-loop simulation environments requiring high-frequency streaming input.

#### Configuration

```python
{
    "type": "kafka",
    "config": {
        "topic": "digital-twin",
        "bootstrap_servers": "localhost:9092",
        "group_id": "my-consumer-group",
        "interpolation": "linear",
        "timeout": 2, # timeout for consuming messages
        "kafka_backend_conf":"path_to/backend_config.json"
    }
}
```
The configuration dictionary is parsed into a `KafkaHandlerConfig` dataclass (where data types are enforced) via `KafkaHandlerConfig.from_dict()`. The `"kafka_backend_conf"` argument allows to kafka network-specific configuration as a separate JSON. Example `backend_config.json` with the available arguments:

```json
{
    "first_msg_timeout": 35,
    "first_delay": 4,
    "max_retries": 3,
    "retry_delay": 0.02,
    "offset_reset": "earliest",
    "max_buffer_len": 10,
    "thread_lifetime": 1000000,
}
```

#### Internal Architecture

To manage Kafka consumption robustly and efficiently, the handler relies on utility components from `kafka_utils.py`:

##### `KafkaHandlerConfig`

* A dataclass that encapsulates all Kafka-related configuration fields (e.g., topic, group ID, server URL).
* Used to validate and control default values for incoming configuration data.
* It also reads and parses optional network-related configuration from a separate JSON.

##### `KafkaThreadManager`

* Manages a background thread that continuously consumes Kafka messages.
* To ensure modularity it calls **a user-defined callback** (e.g. `KafkaDataStreamHandler._handle_message`) for each message received. 
* Supports thread lifecycle control via `start()` and `stop()` methods.
* Avoids blocking the main simulation loop.
* Works in an independent and separated thread. 

#####  `parse_kafka_message(msg)`

* Parses raw Kafka messages into a CoFMPy compatible Python `dict` with a `t` field (timestamp) and associated values under alias keys.
* If a different incoming data structure is used, this function provides an interface to the rest of the API.
* Falls back to raw string output on failure, allowing standalone use of the data handler.

#### Lifecycle

1. **Initialization:**

   * The consumer is instantiated with topic subscription (lazy) using `_create_consumer()`.
   * The thread manager is started via `start_consumer()`, triggering background consumption.

2. **Message Handling:**

   * For the first message, the consumption loop retries until `first_msg_timeout` is reached, pausing for `first_delay` between attempts.
   * After the first message is received (to allow for Kafka broker consumer group stabilization, etc.), the loop continues retrying for up to `max_retries` sessions. Each session consists of sequential attempts until `timeout` is reached, with a `retry_delay` pause between each attempt.
   * As new messages arrive, they are parsed and added to self.data in a thread safe way.
   * The data is fetched in `_build_out_dict` method using timestamp (`t`) and the interpolation method.

3. **Data Access:**

   * `get_data(t)` returns the interpolated values at a specific timestamp.
   * Interpolation uses the same `utils.Interpolator` class as other handlers.

4. **Shutdown:**

   * Call `stop_consumer()` when the handler is no longer needed to gracefully stop the background thread and release Kafka resources.

#### Notes

* Kafka topics must publish messages containing a `t` timestamp field when used the default code.
* Otherwise, you can override `_handle_message` and/or `parse_kafka_message` if a custom workflow is required (decoding, data structure, etc.).
* Lazy subscription ensures the consumer is only connected when needed.

---
## 4. Interpolation

All data stream handlers support time-based interpolation when returning values via `get_data(t)`. The interpolation logic is delegated to a shared utility class: `Interpolator`, located in the `utils` module.

### Supported Methods

* `"previous"` (default): Returns the most recent known value at or before time `t`.
* `"linear"`: Performs linear interpolation between the two closest known timestamps.
* Additional methods are supported by the `Interpolator` class but will raise a warning since not tested in integration.
* Custom methods may be implemented using the `Interpolator` class.

### Usage

Interpolation is configured per handler using the `interpolation` field in the config:

```json
"interpolation": "linear"
```

This setting is passed to the `Interpolator` instance during handler initialization. Each handler is responsible for how and when to invoke the interpolator, typically inside the `get_data(t)` method.

---
## 5. Extending with Custom Handlers

You can add support for new data sources by implementing a custom subclass of `BaseDataStreamHandler`:

1. **Subclass `BaseDataStreamHandler`**
   Implement the abstract methods:

   * `__init__(self, config)`
   * `get_data(self, t: float)`
   * `is_equivalent_stream(self, config: dict)`

2. **Set a unique `type_name`**
   This will be used in the configuration to identify your handler.

3. **Register the handler**
   At module load time (e.g., in your custom handler file):

   ```python
   BaseDataStreamHandler.register_handler(MyCustomHandler)
   ```

4. **Use via configuration**
   Once registered, the handler can be created using the factory method:

   ```python
   handler = BaseDataStreamHandler.create_handler(config_dict)
   ```

### Tips

* Use `add_variable()` to support alias mapping if integrattion with other CoFMPy modules is required.
* Follow the same interpolation pattern as built-in handlers for consistency.
* Use `is_equivalent_stream()` to help avoid redundant handler instances.

