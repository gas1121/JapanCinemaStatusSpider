from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.showing import Showing
from models.showing_booking import ShowingBooking
from models.movie import Movie
from models.cinema import Cinema


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
        showing_booking_dict = {k: v for k, v in dict.items() if k != 'ts'}
        showing_dict = showing_booking_dict['showing']
        # try to get real_title from database
        showing_booking_dict['showing']['real_title'] = Movie.get_by_title(
            Session, showing_dict['title'])
        # get total_seat_count from database
        showing_booking_dict['showing']['total_seat_count'] = \
            Cinema.get_screen_seat_count(
                Session,
                cinema_name=showing_dict['cinema_name'],
                cinema_site=showing_dict['cinema_site'],
                screen=showing_dict['screen'])
        # if SoldOut, change book_seat_count
        if showing_booking_dict['book_status'] == 'SoldOut':
            showing_booking_dict['book_seat_count'] = showing_booking_dict[
                'showing']['total_seat_count']

        showing_booking = ShowingBooking.from_item(
            Session, showing_booking_dict)
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
