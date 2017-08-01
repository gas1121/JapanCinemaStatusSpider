"""
Persist level for JapanCinemaStatusSpider
"""
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from jcssutils.db_utils import db_connect
from crawler.models.cinema import Cinema
from crawler.models.showing import Showing
from crawler.models.showing_booking import ShowingBooking
from crawler.models.movie import Movie


# global session for project
Session = scoped_session(sessionmaker(bind=db_connect()))
