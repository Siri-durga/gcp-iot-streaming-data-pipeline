# Architecture

## Components

- **Producer**: Python script generating random sensor data.
- **Pub/Sub**: Local emulator acting as message broker.
- **Consumer**: Python script validating and inserting data into MySQL.
- **MySQL**: Relational database for storage.

## Data Flow

1. Producer generates JSON payload.
2. Producer publishes to `iot-sensor-data-raw`.
3. Consumer pulls message.
4. Consumer validates schema and ranges.
5. Consumer batches inserts to MySQL.
