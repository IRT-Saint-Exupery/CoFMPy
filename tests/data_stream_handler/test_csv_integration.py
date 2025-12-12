import pytest
from unittest.mock import patch
from cofmupy.data_stream_handler import CsvDataStreamHandler


class CsvHandlerSeparated(CsvDataStreamHandler):
    """Custom class to test one-handler-instance
    per csv file ("separated") behaviour"""

    def _is_equivalent_stream(self, config):
        return False


def test_csv_integration_separated(csv_two_resistors_test, run_integration_test):
    config, expected_results = csv_two_resistors_test(combined=False)

    with patch("cofmupy.data_stream_handler.CsvDataStreamHandler", CsvHandlerSeparated):
        run_integration_test(config, expected_results)


def test_csv_integration_combined(csv_two_resistors_test, run_integration_test):
    config, expected_results = csv_two_resistors_test(combined=True)
    run_integration_test(config, expected_results)
