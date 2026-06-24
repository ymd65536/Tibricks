import os
import sys
from datetime import datetime
from typing import Optional

import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> pymysql.connections.Connection:
    host = os.getenv("TIDB_HOST")
    port = int(os.getenv("TIDB_PORT", "4000"))
    user = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    database = os.getenv("TIDB_DATABASE", "sample")

    if not all([host, user, password]):
        raise ValueError("Missing required TiDB connection environment variables")

    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        connect_timeout=10,
    )


def ensure_schema(connection: pymysql.connections.Connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_events (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                pod_name VARCHAR(64) NOT NULL,
                event_time DATETIME NOT NULL,
                metric_value DOUBLE NOT NULL,
                payload VARCHAR(255) NOT NULL
            )
            """
        )
    connection.commit()


def insert_sample_data(connection: pymysql.connections.Connection, pod_name: str, count: int) -> int:
    with connection.cursor() as cursor:
        inserted = 0
        for index in range(count):
            event_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            payload = f"pod={pod_name} event={index}"
            cursor.execute(
                """
                INSERT INTO sensor_events (pod_name, event_time, metric_value, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (pod_name, event_time, 10.0 + index, payload),
            )
            inserted += 1
        connection.commit()
    return inserted


def main() -> None:
    pod_name = os.getenv("POD_NAME", os.getenv("HOSTNAME", "local"))
    batch_size = int(os.getenv("BATCH_SIZE", "10"))

    connection = get_connection()
    try:
        ensure_schema(connection)
        inserted = insert_sample_data(connection, pod_name, batch_size)
        print(f"Inserted {inserted} rows into TiDB from {pod_name}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
