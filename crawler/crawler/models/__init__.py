"""
Persist level for JapanCinemaStatusSpider
"""
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from jcssutils.db_utils import db_connect as _db_connect
from crawler import settings


def db_connect():
    _db_connect(settings.DATABASE)


# global session for project
Session = scoped_session(sessionmaker(bind=db_connect()))

from crawler.models.cinema import Cinema
from crawler.models.showing import Showing
from crawler.models.showing_booking import ShowingBooking
from crawler.models.movie import Movie
