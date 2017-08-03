from kafka_monitor_plugins.base_handler import BaseHandler

from models import create_table, db_connect, drop_table_if_exist
from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking


class DbManageHandler(BaseHandler):
    schema = "dbmanage_schema.json"

    def setup(self, settings):
        """
        Setup db connection
        """
        self.engine = db_connect()
        self.logger.debug("Connected to Database in {}".format(
            self.__class__.__name__))
        self.table_map = {
            'all': [Cinema, Movie, ShowingBooking, Showing],
            'movie': [Movie],
            'cinema': [Cinema],
            'showing': [ShowingBooking, Showing]
        }

    def handle(self, dict):
        """
        Processes a vaild database manage request

        @param dict: a valid dictionary object
        """
        action = dict['action']
        target = dict['target']
        if action in ['clear', 'init']:
            # drop target table for cleaning data
            for table_class in self.table_map[target]:
                drop_table_if_exist(self.engine, table_class)
            # create table
            create_table(self.engine)
        self.logger.info('db action finished', extra=dict)
