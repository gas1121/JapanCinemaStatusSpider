from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.cinema import Cinema


class CrawledCinemaHandler(BaseHandler):
    schema = "crawled_cinema_schema.json"

    def setup(self, settings):
        """
        Setup db connection
        """
        self.engine = db_connect()
        self.logger.debug("Connected to Database in {}".format(
            self.__class__.__name__))

    def handle(self, dict):
        """
        Processes a vaild database manage request

        @param dict: a valid dictionary object
        """
        # remove 'ts' item in input dict
        cinema_dict = {k: v for k, v in dict.items() if k != 'ts'}
        cinema = Cinema(**cinema_dict)
        exist_cinema = Cinema.get_cinema_if_exist(cinema)
        if exist_cinema:
            # if cinema exists in database, check if it should be merged
            # to exist record.
            # merge strategy:
            # - if exist data is crawled from other source, only add names
            # and screens to exist data;
            # - if cinema do not have site url, item is treated as duplicate
            # and dropped;
            # - otherwise, merge all data
            if cinema.source != exist_cinema.source:
                # replace when new cinema data crawled more screens
                if cinema.screen_count > exist_cinema.screen_count:
                    cinema = Cinema.merge(
                        exist_cinema, cinema,
                        merge_method=Cinema.MergeMethod.replace)
                else:
                    cinema = Cinema.merge(
                        exist_cinema, cinema,
                        merge_method=Cinema.MergeMethod.info_only)
            elif cinema.site:
                cinema = Cinema.merge(
                    exist_cinema, cinema,
                    merge_method=Cinema.MergeMethod.update_count)
        try:
            add_item_to_database(Session, cinema)
            self.logger.info('Cinema added to database', extra=dict)
        except:
            self.logger.info('Cinema failed add to database', extra=dict)
