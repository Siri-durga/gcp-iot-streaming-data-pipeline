import os
import time
import json
import logging
import threading
from concurrent.futures import TimeoutError
from datetime import datetime
from queue import Queue, Empty
from typing import List, Tuple

from google.cloud import pubsub_v1
import mysql.connector
from mysql.connector import Error
from dateutil import parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'test-project')
    TOPIC_ID = os.getenv('PUBSUB_TOPIC_RAW', 'iot-sensor-data-raw')
    SUBSCRIPTION_ID = 'iot-sensor-sub'
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'secret')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'iot_data')
    BATCH_SIZE = 10
    BATCH_TIMEOUT = 5  # seconds

class Databasehandler:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE
            )
            if self.connection.is_connected():
                logging.info("Connected to MySQL database")
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            self.connection = None

    def insert_batch(self, values: List[tuple]) -> bool:
        if not self.connection or not self.connection.is_connected():
            logging.warning("Database connection lost, reconnecting...")
            self.connect()
            if not self.connection:
                logging.error("Failed to reconnect to database.")
                return False

        query = """
        INSERT INTO sensor_readings 
        (device_id, timestamp_utc, temperature_celsius, humidity_percent, processing_timestamp_utc)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, values)
            self.connection.commit()
            logging.info(f"Successfully inserted {cursor.rowcount} records")
            cursor.close()
            return True
        except Error as e:
            logging.error(f"Failed to insert batch: {e}")
            return False

def validate_message(data: dict) -> dict:
    """Validates the incoming message data."""
    required_fields = ['device_id', 'timestamp_utc', 'temperature_celsius', 'humidity_percent']
    
    # Check existence
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
            
    # Check types and simple conversions
    try:
        device_id = str(data['device_id'])
        if not device_id:
             raise ValueError("device_id is empty")
             
        timestamp = parser.isoparse(data['timestamp_utc'])
        
        temp = float(data['temperature_celsius'])
        humidity = float(data['humidity_percent'])
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Type conversion error: {e}")

    # Range checks
    if not (-50 <= temp <= 100):
        raise ValueError(f"Temperature {temp} out of range (-50 to 100)")
        
    if not (0 <= humidity <= 100):
        raise ValueError(f"Humidity {humidity} out of range (0 to 100)")

    return {
        'device_id': device_id,
        'timestamp_utc': timestamp,
        'temperature_celsius': temp,
        'humidity_percent': humidity,
        'processing_timestamp_utc': datetime.utcnow()
    }

def worker(queue: Queue, db_handler: Databasehandler):
    batch_messages = []
    batch_data = []
    last_flush_time = time.time()

    while True:
        try:
            # Wait for message with timeout to allow periodic flushing
            item = queue.get(timeout=1)
            message, valid_data = item
            
            batch_messages.append(message)
            batch_data.append((
                valid_data['device_id'],
                valid_data['timestamp_utc'],
                valid_data['temperature_celsius'],
                valid_data['humidity_percent'],
                valid_data['processing_timestamp_utc']
            ))
            
        except Empty:
            pass
            
        current_time = time.time()
        is_batch_full = len(batch_data) >= Config.BATCH_SIZE
        is_timeout = (current_time - last_flush_time) >= Config.BATCH_TIMEOUT and len(batch_data) > 0
        
        if is_batch_full or is_timeout:
            if batch_data:
                logging.info(f"Flushing batch of {len(batch_data)} records...")
                success = db_handler.insert_batch(batch_data)
                
                if success:
                    for msg in batch_messages:
                        msg.ack()
                else:
                    logging.error("Batch insertion failed. NACKing messages to retry.")
                    for msg in batch_messages:
                        msg.nack()
                
                batch_data = []
                batch_messages = []
                last_flush_time = current_time

def main():
    db_handler = Databasehandler()
    # Wait loop for DB to be ready
    retries = 10
    while not db_handler.connection and retries > 0:
        logging.info("Waiting for database...")
        time.sleep(5)
        db_handler.connect()
        retries -= 1
        
    if not db_handler.connection:
        logging.critical("Could not connect to database. Exiting.")
        return

    message_queue = Queue()
    
    # Start worker thread
    worker_thread = threading.Thread(target=worker, args=(message_queue, db_handler), daemon=True)
    worker_thread.start()

    # Subscriber setup
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(Config.PROJECT_ID, Config.SUBSCRIPTION_ID)
    topic_path = subscriber.topic_path(Config.PROJECT_ID, Config.TOPIC_ID)

    # Create subscription if not exists (for emulator)
    try:
        subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
        logging.info(f"Created subscription {subscription_path}")
    except Exception:
        logging.info(f"Subscription {subscription_path} already exists or error.")

    def callback(message: pubsub_v1.subscriber.message.Message):
        try:
            data = json.loads(message.data.decode("utf-8"))
            valid_data = validate_message(data)
            message_queue.put((message, valid_data))
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Invalid message data: {e} - Data: {message.data}")
            # Ack invalid messages so they don't clog the queue, effectively "Dead Lettering" to logs
            message.ack()
        except Exception as e:
            logging.error(f"Unexpected error in callback: {e}")
            message.nack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    logging.info(f"Listening for messages on {subscription_path}...")

    with subscriber:
        try:
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()
        except Exception as e:
            logging.error(f"Streaming pull failed: {e}")
            streaming_pull_future.cancel()

if __name__ == "__main__":
    main()
