"""Methods pertaining to weather data"""
from enum import IntEnum
import json
import logging
from pathlib import Path
import random
import urllib.parse

import requests
from confluent_kafka import avro

import config
from producers.models.producer import Producer


logger = logging.getLogger(__name__)


class Weather(Producer):
    """Defines a simulated weather model"""

    status = IntEnum(
        "status", "sunny partly_cloudy cloudy windy precipitation", start=0
    )

    rest_proxy_url = config.REST_PROXY_URL

    key_schema = avro.load(f"{Path(__file__).parents[0]}/schemas/weather_key.json")
    value_schema = avro.load(f"{Path(__file__).parents[0]}/schemas/weather_value.json")

    winter_months = set((0, 1, 2, 3, 10, 11))
    summer_months = set((6, 7, 8))

    def __init__(self, month):
        topic_name = config.TOPIC_NAME_WEATHER
        super().__init__(
            topic_name,
            key_schema=Weather.key_schema,
            value_schema=Weather.value_schema,
            num_partitions=1,  # todo
            num_replicas=1,  # todo
        )

        self.status = Weather.status.sunny
        self.temp = 70.0
        if month in Weather.winter_months:
            self.temp = 40.0
        elif month in Weather.summer_months:
            self.temp = 85.0

    def _set_weather(self, month):
        """Returns the current weather"""
        mode = 0.0
        if month in Weather.winter_months:
            mode = -1.0
        elif month in Weather.summer_months:
            mode = 1.0
        self.temp += min(max(-20.0, random.triangular(-10.0, 10.0, mode)), 100.0)
        self.status = random.choice(list(Weather.status))

    def run(self, month):
        self._set_weather(month)
        resp = requests.post(
            url=f"{Weather.rest_proxy_url}/topics/{self.topic_name}",
            headers={"Content-Type": "application/vnd.kafka.avro.v2+json"},
            data=json.dumps(
                {
                    'key_schema': str(Weather.key_schema),
                    'value_schema': str(Weather.value_schema),
                    'records': [
                        {'key': {'timestamp': self.time_millis()},
                         'value': {'temperature': self.temp, 'status': self.status.name}}
                    ]
                }
            ),
        )
        resp.raise_for_status()

        logger.debug(f"sent weather data to kafka, temp: {self.temp}, status: {self.status.name}")
