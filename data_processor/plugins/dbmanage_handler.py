from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, Session
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

    def handle(self, dict):
        pass
