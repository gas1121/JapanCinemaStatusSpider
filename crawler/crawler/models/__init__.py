"""
Persist level for JapanCinemaStatusSpider
"""

from crawler.models.models import (create_table, drop_table_if_exist,
                                         db_connect, Session)
from crawler.models.cinema import Cinema
from crawler.models.showing import Showing
from crawler.models.showing_booking import ShowingBooking
from crawler.models.movie import Movie
