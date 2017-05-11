"""
Persist level for JapanCinemaStatusSpider
"""

from scrapyproject.models.models import (create_table, drop_table_if_exist,
                                         db_connect, Session)
from scrapyproject.models.cinema import Cinema
from scrapyproject.models.showing import Showing
from scrapyproject.models.showing_booking import ShowingBooking
from scrapyproject.models.movie import Movie
