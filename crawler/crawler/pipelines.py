# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scutils.log_factory import LogFactory

# TODO models rework
#from jcssutils import (drop_table_if_exist, create_table)
#from crawler.models import (db_connect, Cinema, Showing, ShowingBooking,
#                            Movie, Session)
from crawler.items import (CinemaItem, ShowingItem, ShowingBookingItem,
                           MovieItem)
from crawler.utils import (use_cinema_database,
                           use_showing_database,
                           use_movie_database)


class DataBasePipeline(object):
    """
    pipeline to add item to database
    will keep exist data if spider has attribute 'keep_old_data'
    """
    def __init__(self, logger, database):
        # TODO change db management as we now use scrapy cluster
        self.logger = logger
        self.database = database
        # keep crawled movie to sum cinema count
        self.crawled_movies = {}
        self.logger.debug("Setup before DataBasePipeline")

    @classmethod
    def from_settings(cls, settings):
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        logger = LogFactory.get_instance(json=my_json,
                                         name=my_name,
                                         stdout=my_output,
                                         level=my_level,
                                         dir=my_dir,
                                         file=my_file,
                                         bytes=my_bytes,
                                         backups=my_backups)

        return cls(logger, database=settings.get('DATABASE'))

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
        self.logger.debug(item)
        if isinstance(item, CinemaItem):
            return self.process_cinema_item(item, spider)
        elif isinstance(item, ShowingItem):
            return self.process_showing_item(item, spider)
        elif isinstance(item, ShowingBookingItem):
            return self.process_showing_booking_item(item, spider)
        elif isinstance(item, MovieItem):
            return self.process_movie_item(item, spider)

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
