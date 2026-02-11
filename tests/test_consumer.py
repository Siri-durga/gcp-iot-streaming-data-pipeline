import unittest
import sys
import os
from dateutil import parser

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consumer.app import validate_message

class TestConsumer(unittest.TestCase):
    def test_valid_message(self):
        data = {
            "device_id": "test-1",
            "timestamp_utc": "2023-10-01T10:00:00Z",
            "temperature_celsius": 20.5,
            "humidity_percent": 50.0
        }
        valid = validate_message(data)
        self.assertEqual(valid['device_id'], "test-1")
        self.assertEqual(valid['temperature_celsius'], 20.5)

    def test_missing_field(self):
        data = {"device_id": "test-1"}
        with self.assertRaises(ValueError):
            validate_message(data)

    def test_out_of_range_temp(self):
        data = {
            "device_id": "test-1",
            "timestamp_utc": "2023-10-01T10:00:00Z",
            "temperature_celsius": 200.0,
            "humidity_percent": 50.0
        }
        with self.assertRaises(ValueError):
            validate_message(data)

if __name__ == '__main__':
    unittest.main()
