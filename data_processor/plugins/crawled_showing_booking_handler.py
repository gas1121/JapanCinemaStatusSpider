from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.showing import Showing
from models.showing_booking import ShowingBooking


class CrawledShowingBookingHandler(BaseHandler):
    # TODO modify scrapy-cluster to support use relative schema file
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

        showing_booking = ShowingBooking.from_item(showing_dict)
        # if showing exists use its id in database
        exist_showing = Showing.get_showing_if_exist(
            Session, showing_booking.showing)
        if exist_showing:
            showing_booking.showing.showing_id = exist_showing.showing_id
            # TODO check if copy id is enabled
            """
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
            """
        # then add self
        try:
            add_item_to_database(Session, showing_booking)
            self.logger.info('ShowingBooking added to database', extra=dict)
        except:
            self.logger.info(
                'ShowingBooking failed add to database', extra=dict)
