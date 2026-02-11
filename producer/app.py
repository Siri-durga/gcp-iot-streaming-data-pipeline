import os
import time
import json
import random
import logging
from datetime import datetime
from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'test-project')
TOPIC_ID = os.getenv('PUBSUB_TOPIC_RAW', 'iot-sensor-data-raw')
PUBLISH_INTERVAL = 1  # seconds

def generate_sensor_data(device_id: str) -> dict:
    """Generates simulated IoT sensor data."""
    return {
        "device_id": device_id,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "temperature_celsius": round(random.uniform(-10.0, 40.0), 2),
        "humidity_percent": round(random.uniform(20.0, 90.0), 2)
    }

def publish_message(publisher, topic_path, data):
    """Publishes a message to the Pub/Sub topic."""
    json_data = json.dumps(data).encode("utf-8")
    
    try:
        future = publisher.publish(topic_path, json_data)
        message_id = future.result()
        logging.info(f"Published message ID {message_id}: {data}")
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")

def main():
    # Initialize Pub/Sub publisher
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    logging.info(f"Starting producer for topic: {topic_path}")

    # Simulate multiple devices
    devices = ["device-001", "device-002", "device-003"]

    while True:
        try:
            device_id = random.choice(devices)
            data = generate_sensor_data(device_id)
            publish_message(publisher, topic_path, data)
            time.sleep(PUBLISH_INTERVAL)
        except KeyboardInterrupt:
            logging.info("Producer stopped by user.")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            time.sleep(5)  # Backoff on error

if __name__ == "__main__":
    main()
