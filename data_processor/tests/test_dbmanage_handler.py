import unittest
from mock import MagicMock, patch

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler


class TestPlugins(unittest.TestCase):
    @patch('plugins.dbmanage_handler.db_connect')
    @patch('plugins.dbmanage_handler.drop_table_if_exist')
    @patch('plugins.dbmanage_handler.create_table')
    def test_dbmanage_handler(self, create_table_mock,
                              drop_table_if_exist_mock,
                              db_connect_mock):
        handler = DbManageHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        handler.table_map = {
            'all': [Cinema, Movie, ShowingBooking, Showing],
            'movie': [Movie],
            'cinema': [Cinema],
            'showing': [ShowingBooking, Showing]
        }
        data = {
            "action": "init",
            "target": "all"
        }
        handler.handle(data)
        self.assertEqual(drop_table_if_exist_mock.call_count, 4)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Cinema)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Movie)
        drop_table_if_exist_mock.assert_any_call(
            handler.engine, ShowingBooking)
        drop_table_if_exist_mock.assert_any_call(handler.engine, Showing)
        create_table_mock.assert_called_once_with(handler.engine)
