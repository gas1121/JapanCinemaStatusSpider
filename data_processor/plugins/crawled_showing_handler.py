from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.showing import Showing


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
        showing = Showing.from_item(showing_dict)
        # if data do not exist in database, add it
        if not Showing.get_showing_if_exist(Session, showing):
            try:
                add_item_to_database(Session, showing)
                self.logger.info('Showing added to database', extra=dict)
            except:
                self.logger.info('Showing failed add to database', extra=dict)
