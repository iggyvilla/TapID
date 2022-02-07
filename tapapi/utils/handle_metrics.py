import json
from datetime import datetime


def handle_metrics(conn, event_name: str, metric_data: dict) -> None:
    with conn:
        with conn.cursor() as curs:
            curs.execute(
                "insert into metrics ( event_name, metric_data, timestamp ) values ( %s, %s, %s )",
                (event_name, json.dumps(metric_data), datetime.now())
            )
