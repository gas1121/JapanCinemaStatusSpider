import unittest
from mock import MagicMock, patch
import arrow

from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking


class TestMovie(unittest.TestCase):
    def test_get_by_title(self):
        session = MagicMock()
        func_mock = session.query().all
        title = "test"

        func_mock.return_value = []
        result = Movie.get_by_title(session, title)
        self.assertEqual(result, None)

        func_mock.return_value = [("test",), ("tes",)]
        result = Movie.get_by_title(session, title)
        self.assertEqual(result, title)

        func_mock.return_value = [("othertitle",), ("tttttttt",)]
        result = Movie.get_by_title(session, title)
        self.assertEqual(result, None)


class TestShowing(unittest.TestCase):
    @patch('models.cinema.Cinema.get_screen_seat_count')
    @patch('models.movie.Movie.get_by_title')
    def test_from_item(self, get_by_title_mock, get_screen_seat_count_mock):
        get_by_title_mock.return_value = "Your Name."
        get_screen_seat_count_mock.return_value = 300
        item = {
            "title": "Your Name.",
            "title_en": "Your Name.",
            "start_time": arrow.get(
                "201608271200", 'YYYYMMDDhhmm').format(),
            "end_time": arrow.get("201608271400", 'YYYYMMDDhhmm').format(),
            "cinema_name": "test_cinema",
            "cinema_site": "test_site",
            "screen": "test_screen",
            "seat_type": "FreeSeat",
            "source": "test_source",
        }
        session = MagicMock()
        showing = Showing.from_item(session, item)
        self.assertEqual(showing.real_title, 'Your Name.')
        self.assertEqual(showing.total_seat_count, 300)
        pass


class TestShowingBooking(unittest.TestCase):
    def test_from_item(self):
        item = {
            'book_status': 'PlentyLeft',
            'book_seat_count': 42,
            'minutes_before': 322,
            'record_time': arrow.get("201608271400", 'YYYYMMDDhhmm').format(),
            'showing': {
                "title": "Your Name.",
                "title_en": "Your Name.",
                "start_time": arrow.get(
                    "201608271200", 'YYYYMMDDhhmm').format(),
                "end_time": arrow.get("201608271400", 'YYYYMMDDhhmm').format(),
                "cinema_name": "test_cinema",
                "cinema_site": "test_site",
                "screen": "test_screen",
                "seat_type": "FreeSeat",
                "source": "test_source",
            },
        }
        session = MagicMock()
        showing_booking = ShowingBooking.from_item(session, item)
        self.assertEqual(showing_booking.book_status, 'PlentyLeft')
        self.assertEqual(showing_booking.showing.screen, 'test_screen')
        pass
