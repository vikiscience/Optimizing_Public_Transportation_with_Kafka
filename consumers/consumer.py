"""Defines core consumer functionality"""
import logging
import socket
from typing import List

from confluent_kafka import Consumer, TopicPartition, OFFSET_BEGINNING
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.avro.serializer import SerializerError
from tornado import gen

import config


logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Defines the base kafka consumer class"""

    def __init__(
        self,
        topic_name_pattern,
        message_handler,
        is_avro=True,
        offset_earliest=False,
        sleep_secs=1.0,
        consume_timeout=0.1,
    ):
        """Creates a consumer object for asynchronous use"""

        self.topic_name_pattern = topic_name_pattern
        self.message_handler = message_handler
        self.sleep_secs = sleep_secs
        self.consume_timeout = consume_timeout
        self.offset_earliest = offset_earliest

        self.broker_properties = {
            'bootstrap.servers': config.BROKER_URL,
            'group.id': 'consumer-group-' + self.topic_name_pattern.replace('^', ''),
            'client.id': 'consumer-' + socket.gethostname(),
            'compression.type': "none",
            'enable.idempotence': "true",
            # 'max.poll.interval.ms': '3600000'  # todo 1 hour?
        }

        # Create the Consumer, using the appropriate type.
        if is_avro is True:
            self.broker_properties["schema.registry.url"] = config.SCHEMA_REGISTRY_URL
            self.consumer = AvroConsumer(self.broker_properties)
        else:
            self.consumer = Consumer(self.broker_properties)

        # Configure the AvroConsumer and subscribe to the topics.
        self.consumer.subscribe(topics=[self.topic_name_pattern], on_assign=self.on_assign)

    def on_assign(self, consumer, partitions: List[TopicPartition]):
        """Callback for when topic assignment takes place"""

        for partition in partitions:
            # If the topic is configured to use `offset_earliest`, set the partition offset to the beginning or earliest
            if self.offset_earliest:
                partition.offset = OFFSET_BEGINNING

        logger.info("Partitions assigned for %s", self.topic_name_pattern)
        consumer.assign(partitions)

    async def consume(self):
        """Asynchronously consumes data from kafka topic"""
        while True:
            num_results = 1
            while num_results > 0:
                num_results = self._consume()
            await gen.sleep(self.sleep_secs)

    def _consume(self):
        """Polls Kafka for messages. Returns 1 if a message was received, 0 otherwise"""

        try:
            msg = self.consumer.poll(timeout=self.consume_timeout)  # in sec
        except SerializerError as e:
            logger.error(e)
            msg = None

        if msg is None:
            pass
        elif msg.error() is not None:
            logger.error(msg.error())
        else:
            self.message_handler(msg)
            return 1
        return 0

    def close(self):
        """Cleans up any open kafka consumers"""
        self.consumer.unassign()
        self.consumer.unsubscribe()
        self.consumer.close()
