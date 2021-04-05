"""Defines a Tornado Server that consumes Kafka Event data for display"""
import logging
import logging.config as logging_config
from pathlib import Path

import tornado.ioloop
import tornado.template
import tornado.web


# Import logging before models to ensure configuration is picked up
logging_config.fileConfig(f"{Path(__file__).parents[0]}/logging.ini")

import config
from consumers.consumer import KafkaConsumer
from consumers.models import Lines, Weather
from consumers.topic_check import Checker


logger = logging.getLogger(__name__)
checker = Checker()


class MainHandler(tornado.web.RequestHandler):
    """Defines a web request handler class"""

    template_dir = tornado.template.Loader(f"{Path(__file__).parents[0]}/templates")
    template = template_dir.load("status.html")

    def initialize(self, weather, lines):
        """Initializes the handler with required configuration"""
        self.weather = weather
        self.lines = lines

    def get(self):
        """Responds to get requests"""
        logger.debug("Rendering and writing handler template")
        self.write(MainHandler.template.generate(weather=self.weather, lines=self.lines))


def run_server():
    """Runs the Tornado Server and begins Kafka consumption"""
    if checker.topic_exists(config.TOPIC_NAME_TURNSTILE_SUMMARY) is False:
        logger.fatal("Ensure that the KSQL Command has run successfully before running the web server!")
        exit(1)
    if checker.topic_exists(config.TOPIC_NAME_TRANS_STATIONS) is False:
        logger.fatal("Ensure that Faust Streaming is running successfully before running the web server!")
        exit(1)

    weather_model = Weather()
    lines = Lines()

    application = tornado.web.Application(
        [(r"/", MainHandler, {"weather": weather_model, "lines": lines})]
    )
    application.listen(8888)

    # Build kafka consumers
    consumers = [
        KafkaConsumer(
            config.TOPIC_NAME_WEATHER,
            weather_model.process_message,
            offset_earliest=True,
        ),
        KafkaConsumer(
            config.TOPIC_NAME_TRANS_STATIONS,
            lines.process_message,
            offset_earliest=True,
            is_avro=False,
        ),
        KafkaConsumer(
            config.TOPIC_NAME_ARRIVAL,
            lines.process_message,
            offset_earliest=True,
        ),
        KafkaConsumer(
            config.TOPIC_NAME_TURNSTILE_SUMMARY,
            lines.process_message,
            offset_earliest=True,
            is_avro=False,
        ),
    ]

    try:
        logger.info("Open a web browser to http://localhost:8888 to see the Transit Status Page")
        for consumer in consumers:
            tornado.ioloop.IOLoop.current().spawn_callback(consumer.consume)

        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        tornado.ioloop.IOLoop.current().stop()
        for consumer in consumers:
            consumer.close()


if __name__ == "__main__":
    run_server()
