"""Producer base-class providing common utilities and functionality"""
import logging
import socket
import time

import config
from confluent_kafka import avro
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.avro import AvroProducer

logger = logging.getLogger(__name__)


class Producer:
    """Defines and provides common functionality amongst Producers"""

    # Tracks existing topics across all Producer instances
    existing_topics = set([])

    def __init__(
        self,
        topic_name,
        key_schema,
        value_schema=None,
        num_partitions=1,
        num_replicas=1,
    ):
        """Initializes a Producer object with basic settings"""
        self.topic_name = topic_name
        self.key_schema = key_schema
        self.value_schema = value_schema
        self.num_partitions = num_partitions
        self.num_replicas = num_replicas

        self.client = AdminClient({'bootstrap.servers': config.BROKER_URL})

        self.broker_properties = {
            'bootstrap.servers': config.BROKER_URL,
            'client.id': socket.gethostname(),
            'compression.type': "none",
            'enable.idempotence': "true",
            'schema.registry.url': config.SCHEMA_REGISTRY_URL
        }

        # If the topic does not already exist, try to create it
        self.topic = NewTopic(self.topic_name, num_partitions=self.num_partitions, replication_factor=self.num_replicas)
        if self.topic_name not in Producer.existing_topics:
            self.create_topic()
            Producer.existing_topics.add(self.topic_name)

        self.producer = AvroProducer(self.broker_properties,
                                     default_key_schema=self.key_schema,
                                     default_value_schema=self.value_schema
                                     )

    def create_topic(self):
        """Creates the producer topic if it does not already exist"""
        self.client.create_topics([self.topic])
        logger.info(f"Topic creation complete: {self.topic_name}")

    @staticmethod
    def time_millis():
        """Use this function to get the key for Kafka Events"""
        return int(round(time.time() * 1000))

    def close(self):
        """Prepares the producer for exit by cleaning up the producer"""
        # self.client.delete_topics(list(Producer.existing_topics))  # todo delete weather topic
        self.producer.flush(timeout=1)
        logger.info("Producer close complete")
