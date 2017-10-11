from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.showing import Showing
from models.movie import Movie
from models.cinema import Cinema


class CrawledShowingHandler(BaseHandler):
    schema = "crawled_showing_schema.json"

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
        showing_dict = {k: v for k, v in dict.items() if k != 'ts'}
        # try to get real_title from database
        showing_dict['real_title'] = Movie.get_by_title(
            Session, showing_dict['title'])
        # get total_seat_count from database
        showing_dict['total_seat_count'] = Cinema.get_screen_seat_count(
            Session,
            cinema_name=showing_dict['cinema_name'],
            cinema_site=showing_dict['cinema_site'],
            screen=showing_dict['screen'])

        showing = Showing.from_item(Session, showing_dict)
        # if data do not exist in database, add it
        if not Showing.get_showing_if_exist(Session, showing):
            try:
                add_item_to_database(Session, showing)
                self.logger.info('Showing added to database', extra=dict)
            except:
                self.logger.info('Showing failed add to database', extra=dict)
