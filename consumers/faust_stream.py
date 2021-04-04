"""Defines trends calculations for stations"""
import logging

import faust

import config


logger = logging.getLogger(__name__)


# Faust will ingest records from Kafka in this format
class Station(faust.Record):
    stop_id: int
    direction_id: str
    stop_name: str
    station_name: str
    station_descriptive_name: str
    station_id: int
    order: int
    red: bool
    blue: bool
    green: bool


# Faust will produce records to Kafka in this format
class TransformedStation(faust.Record):
    station_id: int
    station_name: str
    order: int
    line: str


# Define a Faust Stream that ingests data from the Kafka Connect stations topic and
#   places it into a new topic with only the necessary information.
app = faust.App("stations-stream", broker="kafka://localhost:9092", store="memory://")

# Define the input Kafka Topic = output topic of Kafka Connect
topic = app.topic(config.TOPIC_NAME_STATIONS, value_type=Station)

# Define the output Kafka Topic
out_topic = app.topic(config.TOPIC_NAME_TRANS_STATIONS, value_type=TransformedStation, partitions=1)

# Define a Faust Table
table = app.Table(
    "stations-table",
    default=int,
    partitions=1,
    changelog_topic=out_topic,
)


# Using Faust, transform input `Station` records into `TransformedStation` records. Note that
# "line" is the color of the station. So if the `Station` record has the field `red` set to true,
# then you would set the `line` of the `TransformedStation` record to the string `"red"`


def my_foo(e):
    if e.red:
        return "red"
    if e.blue:
        return "blue"
    if e.green:
        return "green"


@app.agent(topic)
async def foo(stream):
    async for e in stream:
        o = TransformedStation(station_id=e.station_id,
                               station_name=e.station_name,
                               order=e.order,
                               line=my_foo(e))
        table[e.station_id] = o


if __name__ == "__main__":
    app.main()
