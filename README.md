# Real-Time IoT Sensor Data Ingestion Pipeline

![CI Status](https://github.com/Siri-durga/gcp-iot-streaming-data-pipeline/actions/workflows/ci.yml/badge.svg)

This project implements a robust, real-time data pipeline for ingesting, validating, and storing simulated IoT sensor data. It leverages Google Cloud Pub/Sub (Emulator) for messaging and MySQL for persistent storage, fully containerized with Docker.

## Project Overview

The pipeline consists of three main components:
1.  **Producer**: Generates simulated sensor data (Temperature, Humidity) and publishes it to a Pub/Sub topic.
2.  **Pub/Sub Emulator**: Acts as the message broker, decoupling the producer and consumer.
3.  **Consumer**: Subscribes to the topic, validates incoming data for quality and schema conformity, and batches valid records into a MySQL database.

## Architecture

Data Flow:
`Producer -> [Pub/Sub Topic: iot-sensor-data-raw] -> Consumer -> (Validation) -> MySQL [Table: sensor_readings]`

Key Features:
-   **Event-Driven**: Independent microservices.
-   **Data Quality**: Strict validation of schema, types, and ranges.
-   **Resilience**: Error handling, retry logic, and NACK/ACK mechanisms.
-   **Performance**: Batch insertion for database efficiency.

## Prerequisites

-   Docker and Docker Compose installed.
-   Python 3.9+ (for local non-docker testing only).

## Setup & Running

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Environment Variables**:
    A `.env.example` is provided. The `docker-compose.yml` has defaults set for local development, so no manual `.env` file creation is strictly necessary for the emulator/local setup.

3.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
    This command will:
    -   Start the MySQL database and initialize the schema.
    -   Start the Pub/Sub emulator.
    -   Build and start the Producer and Consumer services.

4.  **Verify**:
    -   Check the logs to see the producer publishing and consumer inserting:
        ```bash
        docker-compose logs -f
        ```
    -   Access the MySQL database to verify data:
        ```bash
        docker-compose exec mysql mysql -u root -psecret -e "USE iot_data; SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 10;"
        ```

## Data Quality & validation

The Consumer service enforces the following rules:
-   **Schema**: Required fields (`device_id`, `timestamp_utc`, `temperature_celsius`, `humidity_percent`).
-   **Ranges**:
    -   Temperature: -50°C to 100°C.
    -   Humidity: 0% to 100%.
-   **Behavior**: Invalid messages are logged as errors and acknowledged (to prevent infinite loops) but NOT inserted into the database (effectively dropped/dead-lettered via logs).

## Directory Structure

-   `producer/`: Python producer application.
-   `consumer/`: Python consumer application.
-   `docker-compose.yml`: Docker orchestration.
-   `db_init.sql`: Database initialization script.
