# -*- coding: utf-8 -*-
import sys
import traceback
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError
import ujson
from crawler.items import (CinemaItem, ShowingItem, ShowingBookingItem,
                           MovieItem)
from crawler.utils import sc_log_setup
from crawler.utils import (use_cinema_database, use_showing_database)
# TODO showing,cinema models rework


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


class DataBasePipeline(object):
    """
    pipeline to add item to database
    will keep exist data if spider has attribute 'keep_old_data'
    """
    def __init__(self, logger):
        # TODO change db management as we now use scrapy cluster
        self.logger = logger
        self.logger.debug("Setup before DataBasePipeline")

    @classmethod
    def from_settings(cls, settings):
        logger = sc_log_setup(settings)
        return cls(logger)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def open_spider(self, spider):
        self.logger.debug("open_spider in DataBasePipeline")
        # TODO model rework
        """
        engine = db_connect()
        if not spider.keep_old_data:
            # drop data
            if use_showing_database(spider):
                drop_table_if_exist(engine, ShowingBooking)
                drop_table_if_exist(engine, Showing)
            elif use_cinema_database(spider):
                drop_table_if_exist(engine, Cinema)
            elif use_movie_database(spider):
                drop_table_if_exist(engine, Movie)
        create_table(engine)
        """

    def close_spider(self, spider):
        self.logger.debug("close_spider in DataBasePipeline")
        # close global session when spider ends
        # TODO model rework
        """
        Session.remove()
        """

    def process_item(self, item, spider):
        """
        use cinema table if spider has attribute "use_cinema_database"
        use showing table if spider has attribute "use_showing_database"
        a spider should not have both attributes
        """
        self.logger.info("process_item in DataBasePipeline")
        """
        if isinstance(item, CinemaItem):
            return self.process_cinema_item(item, spider)
        elif isinstance(item, ShowingItem):
            return self.process_showing_item(item, spider)
        elif isinstance(item, ShowingBookingItem):
            return self.process_showing_booking_item(item, spider)
        elif isinstance(item, MovieItem):
            return self.process_movie_item(item, spider)
        """
        return item

    def process_cinema_item(self, item, spider):
        # TODO model rework
        """
        cinema = Cinema(**item)
        exist_cinema = Cinema.get_cinema_if_exist(cinema)
        if not exist_cinema:
            # if data do not exist in database, add it
            self.add_item_to_database(cinema)
        else:
            # otherwise check if it should be merged to exist record
            # merge strategy:
            # - if exist data is crawled from other source, only add names
            # and screens to exist data;
            # - if cinema do not have site url, item is treated as duplicate
            # and dropped;
            # - otherwise, merge all data
            if cinema.source != exist_cinema.source:
                # replace when new cinema data crawled more screens
                if cinema.screen_count > exist_cinema.screen_count:
                    exist_cinema.merge(
                        cinema, merge_method=Cinema.MergeMethod.replace)
                else:
                    exist_cinema.merge(
                        cinema, merge_method=Cinema.MergeMethod.info_only)
                self.add_item_to_database(exist_cinema)
            elif cinema.site:
                exist_cinema.merge(
                    cinema, merge_method=Cinema.MergeMethod.update_count)
                self.add_item_to_database(exist_cinema)
        return item
        """
        return item

    def process_showing_item(self, item, spider):
        # TODO model rework
        """
        showing = Showing.from_item(item)
        # if data do not exist in database, add it
        if not Showing.get_showing_if_exist(showing):
            self.add_item_to_database(showing)
        return item
        """
        return item

    def process_showing_booking_item(self, item, spider):
        # TODO model rework
        """
        showing_booking = ShowingBooking.from_item(item)

        # if showing exists use its id in database
        exist_showing = Showing.get_showing_if_exist(showing_booking.showing)
        if exist_showing:
            old_showing = showing_booking.showing
            showing_booking.showing = exist_showing
            showing_booking.showing.title = old_showing.title
            showing_booking.showing.title_en = old_showing.title_en
            showing_booking.showing.start_time = old_showing.start_time
            showing_booking.showing.end_time = old_showing.end_time
            showing_booking.showing.cinema_name = old_showing.cinema_name
            showing_booking.showing.cinema_site = old_showing.cinema_site
            showing_booking.showing.screen = old_showing.screen
            showing_booking.showing.seat_type = old_showing.seat_type
            showing_booking.showing.total_seat_count = \
                old_showing.total_seat_count
            showing_booking.showing.source = old_showing.source
        # then add self
        self.add_item_to_database(showing_booking)
        return item
        """
        return item

    def process_movie_item(self, item, spider):
        # TODO model rework
        """
        movie = Movie(**item)
        exist_movie = Movie.get_movie_if_exist(movie)
        if not exist_movie:
            # if data do not exist in database, add it
            self.add_item_to_database(movie)
        else:
            # sum cinema count
            exist_movie.current_cinema_count += movie.current_cinema_count
            self.add_item_to_database(exist_movie)
        return item
        """
        return item

    def add_item_to_database(self, db_item):
        # TODO model rework
        """
        try:
            db_item = Session.merge(db_item)
            Session.commit()
            self.logger.info("Item added to database")
        except:
            self.logger.info("Commit failed")
            Session.rollback()
            raise
        """
