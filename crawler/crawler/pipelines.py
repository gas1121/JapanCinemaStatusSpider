# -*- coding: utf-8 -*-
import sys
import traceback
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError
import ujson
from crawler.utils import sc_log_setup


class CrawledItemToKafkaPipiline(object):
    """Pipeline to submit crawled item to target kafka topic
    """
    def __init__(self, logger, producer, topic):
        self.logger = logger
        self.logger.debug("Setup {}".format(
            self.__class__.__name__))
        self.producer = producer
        self.topic = topic

    @classmethod
    def from_settings(cls, settings):
        logger = sc_log_setup(settings)
        try:
            producer = KafkaProducer(
                bootstrap_servers=settings['KAFKA_HOSTS'],
                retries=3,
                linger_ms=settings['KAFKA_PRODUCER_BATCH_LINGER_MS'],
                buffer_memory=settings['KAFKA_PRODUCER_BUFFER_BYTES'],
                value_serializer=lambda m: m.encode('utf-8'))
        except Exception as e:
                logger.error("Unable to connect to Kafka in Pipeline"
                             ", raising exit flag.")
                # this is critical so we choose to exit.
                # exiting because this is a different thread from the crawlers
                # and we want to ensure we can connect to Kafka when we boot
                sys.exit(1)
        topic = settings['JCSS_DATA_PROCESSOR_TOPIC']
        return cls(logger, producer, topic)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def open_spider(self, spider):
        self.logger.debug("open_spider in {}".format(
            self.__class__.__name__))

    def close_spider(self, spider):
        self.logger.debug("close_spider in {}".format(
            self.__class__.__name__))
        self.producer.flush()
        self.producer.close(timeout=10)

    def _clean_item(self, item):
        '''
        Cleans the item to be logged
        '''
        item_copy = dict(item)
        item_copy['action'] = 'ack'
        item_copy['logger'] = self.logger.name

        return item_copy

    def _kafka_success(self, item, spider, response):
        '''
        Callback for successful send
        '''
        item['success'] = True
        item = self._clean_item(item)
        item['spiderid'] = spider.name
        self.logger.info("Sent item to Kafka", item)

    def _kafka_failure(self, item, spider, response):
        '''
        Callback for failed send
        '''
        item['success'] = False
        item['exception'] = traceback.format_exc()
        item['spiderid'] = spider.name
        item = self._clean_item(item)
        self.logger.error("Failed to send item to Kafka", item)

    def process_item(self, item, spider):
        self.logger.debug("process_item in {}".format(
            self.__class__.__name__))
        data = dict(item)
        try:
            message = ujson.dumps(data, sort_keys=True)
        except:
            self.logger.error("item failed to dump into json")
        try:
            future = self.producer.send(self.topic, message)
            future.add_callback(self._kafka_success, data, spider)
            future.add_errback(self._kafka_failure, data, spider)
        except KafkaTimeoutError:
            self.logger.warning("Caught KafkaTimeoutError exception")
        return item
