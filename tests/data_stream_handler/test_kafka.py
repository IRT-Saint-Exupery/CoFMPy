# test_kafka_data_stream_handler.py
import pytest
pytest.skip("Skipping this test file", allow_module_level=True)
import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import json
import threading
from cofmpy.data_stream_handler import KafkaDataStreamHandler


class TestKafkaDataStreamHandler(unittest.TestCase):

    def setUp(self):
        self.var_name = "MySignal"
        self.topic = "test_topic"
        self.t_out = 1
        self.config = {
            "topic": self.topic,
            "variable": self.var_name,
            "uri": "localhost:9092",
            "group_id": "test_group",
            "interpolation": "previous",
            "timeout": self.t_out
        }

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.KafkaDataStreamHandler.start_consuming")
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Interpolator")
    def test_init_and_config_validation(self, mock_interp, mock_consumer, mock_start):
        handler = KafkaDataStreamHandler(**self.config)

        self.assertEqual(handler.topic, self.topic)
        self.assertEqual(handler.var_name, self.var_name)
        self.assertEqual(handler.timeout, self.t_out)
        self.assertTrue(isinstance(handler.data, pd.DataFrame))
        self.assertTrue(mock_consumer.called)
        self.assertTrue(mock_interp.called)

        handler.stop_consuming()

    def test_validate_config_defaults(self):
        config = {
            "topic": "t",
            "variable": "v",
            "uri": "server:1234",
            "group_id": "g"
        }
        handler_args = KafkaDataStreamHandler._validate_config(KafkaDataStreamHandler, config)
        positional, optional = handler_args

        self.assertEqual(optional[0], "previous")
        self.assertEqual(optional[1], 2)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_lazy_subscribe(self, mock_consumer):
        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()
        handler._subscribed = False

        handler._lazy_subscribe()
        handler.consumer.subscribe.assert_called_once_with([self.topic])
        self.assertTrue(handler._subscribed)

    def test_parse_kafka_message(self):
        class MockMsg:
            def value(self):
                return b"{'t': 1, 'temperature': 22}"

        result = KafkaDataStreamHandler.parse_kafka_message(MockMsg())
        self.assertEqual(result["t"].iloc[0], 1.0)
        self.assertEqual(result["temperature"].iloc[0], 22.0)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Interpolator")
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_handle_message_updates_data(self, mock_consumer_class, mock_interp_class):
        handler = KafkaDataStreamHandler(**self.config)
        handler.data = pd.DataFrame(columns=["t", "value"])

        # Mock Kafka message
        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b'{"t": 1, "value": 22.5}'

        handler._handle_message(mock_msg)

        self.assertEqual(handler.data.shape[0], 1)
        self.assertIn("value", handler.data.columns)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Interpolator")
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_get_data_interpolates(self, mock_consumer_class, mock_interp_class):
        handler = KafkaDataStreamHandler(**self.config)

        handler.data = pd.DataFrame({
            "t": [1.0, 2.0, 3.0],
            "value": [20.0, 21.0, 22.0]
        })

        handler.timeout = -1  # Skip sleep logic

        mock_interp = MagicMock()
        mock_interp.return_value = [21.5]
        handler.interpolator = mock_interp

        result = handler.get_data(2.5)
        mock_interp.assert_called_once()
        self.assertEqual(result, [21.5])
        
    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.logger")
    def test_handle_message_with_error(self, mock_logger):
        mock_message = MagicMock()
        mock_message.error.return_value = MagicMock(code=lambda: 1)

        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()

        handler._handle_message(mock_message)

        mock_logger.error.assert_called()

    def test_handle_message_valid(self):
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b"{'t': 1, 'temperature': 22}"
        mock_message.offset.return_value = 5

        handler = KafkaDataStreamHandler(**self.config)
        handler.data = pd.DataFrame(columns=["t", "temperature"])
        handler.first_received = None

        handler._handle_message(mock_message)
        self.assertIsNotNone(handler.first_received)
        self.assertIn("temperature", handler.data.columns)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_start_stop_consuming(self, mock_consumer_class):
        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()

        handler.start_consuming()
        self.assertTrue(handler.running)
        self.assertTrue(handler.consumer_thread.is_alive())

        handler.stop_consuming()
        self.assertFalse(handler.running)

    @patch("cofmpy.data_stream_handler.kafka_data_stream_handler.Consumer")
    def test_consume_loop(self, mock_consumer_class):
        handler = KafkaDataStreamHandler(**self.config)
        handler.consumer = MagicMock()
        handler.running = True

        # Simulate poll returning one mock message
        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"{'t': 1, 'temperature': 22}"
        mock_msg.offset.return_value = 3
        handler.consumer.poll = MagicMock(side_effect=[mock_msg, None, None])
        handler._handle_message = MagicMock()
        handler.consumer.close = MagicMock()

        # Run _consume for a short time
        def stop_soon():
            handler.running = False

        threading.Timer(0.1, stop_soon).start()
        handler._consume()

        handler._handle_message.assert_called_with(mock_msg)

