import os
from datetime import datetime

from dotenv import load_dotenv
from pytidb import TiDBClient

load_dotenv()


def main() -> None:
    host = os.getenv("TIDB_HOST")
    port = int(os.getenv("TIDB_PORT", "4000"))
    user = os.getenv("TIDB_USER")
    password = os.getenv("TIDB_PASSWORD")
    database = os.getenv("TIDB_DATABASE", "sample")
    pod_name = os.getenv("POD_NAME", os.getenv("HOSTNAME", "local"))
    batch_size = int(os.getenv("BATCH_SIZE", "10"))

    if not all([host, user, password]):
        raise ValueError("Missing required TiDB connection environment variables")

    client = TiDBClient(host=host, port=port, user=user, password=password, database=database)
    try:
        client.connect()
        client.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_events_pytidb (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                pod_name VARCHAR(64) NOT NULL,
                event_time DATETIME NOT NULL,
                metric_value DOUBLE NOT NULL,
                payload VARCHAR(255) NOT NULL
            )
            """
        )

        inserted = 0
        for index in range(batch_size):
            event_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            payload = f"pod={pod_name} event={index}"
            client.execute(
                """
                INSERT INTO sensor_events_pytidb (pod_name, event_time, metric_value, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (pod_name, event_time, 10.0 + index, payload),
            )
            inserted += 1

        client.commit()
        print(f"Inserted {inserted} rows into TiDB via pytidb from {pod_name}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
