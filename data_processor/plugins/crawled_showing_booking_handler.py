from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.showing import Showing
from models.showing_booking import ShowingBooking


class CrawledShowingBookingHandler(BaseHandler):
    # TODOLATER modify scrapy-cluster to support use relative schema file
    schema = "crawled_showing_booking_schema.json"

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

        showing_booking = ShowingBooking.from_item(Session, showing_dict)
        # if showing exists use its id in database
        exist_showing = Showing.get_showing_if_exist(
            Session, showing_booking.showing)
        if exist_showing:
            showing_booking.showing_id = exist_showing.id
            showing_booking.showing.id = exist_showing.id
        # then add self
        try:
            add_item_to_database(Session, showing_booking)
            self.logger.info('ShowingBooking added to database', extra=dict)
        except:
            self.logger.info(
                'ShowingBooking failed add to database', extra=dict)
