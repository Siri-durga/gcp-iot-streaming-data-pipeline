import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.app import generate_sensor_data

class TestProducer(unittest.TestCase):
    def test_schema_keys(self):
        data = generate_sensor_data("test-device")
        expected_keys = ["device_id", "timestamp_utc", "temperature_celsius", "humidity_percent"]
        for key in expected_keys:
            self.assertIn(key, data)

    def test_value_types(self):
        data = generate_sensor_data("test-device")
        self.assertIsInstance(data['device_id'], str)
        self.assertIsInstance(data['timestamp_utc'], str)
        self.assertIsInstance(data['temperature_celsius'], float)
        self.assertIsInstance(data['humidity_percent'], float)

if __name__ == '__main__':
    unittest.main()
