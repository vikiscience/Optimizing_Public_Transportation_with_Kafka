"""Contains functionality related to Lines"""
import json
import logging

import config
from consumers.models import Line


logger = logging.getLogger(__name__)


class Lines:
    """Contains all train lines"""

    def __init__(self):
        """Creates the Lines object"""
        self.red_line = Line("red")
        self.green_line = Line("green")
        self.blue_line = Line("blue")

    def process_message(self, message):
        """Processes a station message"""
        if message.topic() == config.TOPIC_NAME_TRANS_STATIONS or message.topic() == config.TOPIC_NAME_ARRIVAL:
            value = message.value()
            if message.topic() == config.TOPIC_NAME_TRANS_STATIONS:
                value = json.loads(value)
            if value["line"] == "green":
                self.green_line.process_message(message)
            elif value["line"] == "red":
                self.red_line.process_message(message)
            elif value["line"] == "blue":
                self.blue_line.process_message(message)
            else:
                logger.debug("Discarding unknown line %s, msg %s", value["line"], value)
        elif message.topic() == config.TOPIC_NAME_TURNSTILE_SUMMARY:
            self.green_line.process_message(message)
            self.red_line.process_message(message)
            self.blue_line.process_message(message)
        else:
            logger.info("Ignoring non-lines message %s", message.topic())
