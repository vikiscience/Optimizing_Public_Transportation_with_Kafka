"""
Topic Checker module
"""

import requests
from confluent_kafka.admin import AdminClient
import config


class Checker:
    def __init__(self):
        self.client = AdminClient({"bootstrap.servers": config.BROKER_URL})

    def topic_exists(self, topic):
        """Checks if the given topic exists in Kafka"""
        topic_list = self.get_topics()
        return topic in topic_list

    def get_topics(self):
        """Get list of all Kafka topics"""
        # option 1 - call Rest Proxy API
        resp = requests.get(config.REST_PROXY_URL + '/topics')
        resp.raise_for_status()
        topic_list = resp.json()

        # option 2 - call client
        # topic_metadata = self.client.list_topics(timeout=5)
        # topic_list = list(set(t.topic for t in iter(topic_metadata.topics.values())))
        # print('Available topics from client:', len(topic_list), sorted(topic_list))
        return topic_list

    def delete_topics(self, topic_name: str = None, topic_prefix: str = 'com.udacity'):
        """Delete topics (if no topic name is specified, all topics with a given prefix will be deleted)"""
        if topic_name is None:
            all_topics = self.get_topics()
            topics_to_delete = [t for t in all_topics if t.startswith(topic_prefix)]
        else:
            topics_to_delete = [topic_name]
        print('Following topics will be deleted:')
        for t in topics_to_delete:
            print('\t', t)
        self.client.delete_topics(topics_to_delete)


if __name__ == '__main__':
    checker = Checker()
    topics = checker.get_topics()
    print('Available topics:', len(topics), sorted(topics))
    # checker.delete_topics('TURNSTILE_SUMMARY')
    # checker.delete_topics(topic_prefix='_confluent-ksql-ksql_service_docker')
