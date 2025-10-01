# KafkaThreadManager

`KafkaThreadManager` is a utility class to manage a **background thread** that consumes messages from a Kafka topic using a given Kafka consumer and a user-defined callback.

---

## 1. Initialization

```python
from your_module import KafkaThreadManager

manager = KafkaThreadManager(
    consumer=my_kafka_consumer,
    callback=my_callback_function,
    thread_lifetime=40  # optional, default 40 seconds
)
```

### Parameters

* `consumer` (Kafka consumer object)

  * Typically a `confluent_kafka.Consumer`.
  * Handles connection and message polling from Kafka.

* `callback` (function)

  * Function to process each consumed message.
  * Signature: `callback(msg)` where `msg` is a Kafka message object.
  * **Error handling should be implemented in the callback**.

* `thread_lifetime` (float, optional, default `40`)

  * Maximum time (in seconds) the consuming thread should run.
  * If `None` or `0`, the thread runs indefinitely until `stop()` is called.

---

## 2. Start the consumer thread

```python
manager.start()
```

* Spawns a **daemon thread** to run `_consume_loop`.
* Polls messages from Kafka and calls `callback(msg)` for each message.
* Logs when the thread starts:

  ```
  Kafka consumer started consuming in thread '<thread_name>'
  ```

---

## 3. Consuming loop (`_consume_loop`)

* Runs internally in a separate thread.
* Logic:

    1. Track elapsed time (if `thread_lifetime` is set).
    2. Poll Kafka messages with `consumer.poll(timeout=1)`.  
    **Note:** `poll` is a `confluent_kafka.Consumer` method.
    3. If a message is received, call `callback(msg)`.
    4. Stops when:

        * Thread lifetime is exceeded, or
        * `stop()` is called manually.

* Logs errors during polling and a message when the thread stops.

---

## 4. Stop the thread gracefully

```python
manager.stop()
```

* Sets `running = False`.
* Waits for the thread to finish (`thread.join()`).
* Closes the Kafka consumer.
* Logs: `"Kafka consumer thread stopped."`

---

### ⚠️ Notes

* The **callback function must handle its own exceptions**; otherwise, they propagate to the consuming thread.
* Thread is a **daemon**, so it won’t block Python shutdown if the main program exits.
* Use `thread_lifetime` to limit how long the consumer runs automatically; otherwise, call `stop()` manually.
