import unittest
from mock import MagicMock, patch, call

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
