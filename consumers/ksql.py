"""Configures KSQL to combine station and turnstile data"""
import json
import logging
import requests

import config
from consumers.topic_check import Checker


logger = logging.getLogger(__name__)


# First statement creates a `turnstile` table from the turnstile topic, using 'avro' datatype!
# Second statement creates a `turnstile_summary` table by selecting from the turnstile table and grouping on station_id.
KSQL_STATEMENT = f"""
CREATE TABLE turnstile (
    station_id INTEGER,
    station_name VARCHAR,
    line INTEGER
) WITH (
    KAFKA_TOPIC='{config.TOPIC_NAME_TURNSTILE}',
    VALUE_FORMAT='AVRO',
    KEY='station_id'
);

CREATE TABLE {config.TOPIC_NAME_TURNSTILE_SUMMARY}
WITH (
    KAFKA_TOPIC='{config.TOPIC_NAME_TURNSTILE_SUMMARY}',
    VALUE_FORMAT='JSON'
) AS
    SELECT station_id, count(*) as count FROM turnstile GROUP BY station_id;
"""


def execute_statement():
    """Executes the KSQL statement against the KSQL API"""
    if Checker().topic_exists(config.TOPIC_NAME_TURNSTILE_SUMMARY) is True:
        logger.info(f"Topic exists: {config.TOPIC_NAME_TURNSTILE_SUMMARY} --> exiting...")
        return

    logger.debug("Executing ksql statement...")

    resp = requests.post(
        f"{config.KSQL_URL}/ksql",
        headers={"Content-Type": "application/vnd.ksql.v1+json"},
        data=json.dumps(
            {
                "ksql": KSQL_STATEMENT,
                "streamsProperties": {"ksql.streams.auto.offset.reset": "earliest"},
            }
        ),
    )

    # Ensure that a 2XX status code was returned
    resp.raise_for_status()
    logger.debug(f"Ksql response: {resp.json()}")


if __name__ == "__main__":
    execute_statement()
