import unittest
from mock import MagicMock, patch, call
from copy import deepcopy

from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler
from plugins.crawled_movie_handler import CrawledMovieHandler
from plugins.crawled_cinema_handler import CrawledCinemaHandler


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
        drop_table_if_exist_mock.assert_has_calls([
            call(handler.engine, Cinema),
            call(handler.engine, Movie),
            call(handler.engine, ShowingBooking),
            call(handler.engine, Showing),
        ])
        create_table_mock.assert_called_once_with(handler.engine)

    @patch('models.movie.Movie.get_movie_if_exist')
    @patch('plugins.crawled_movie_handler.add_item_to_database')
    @patch('plugins.crawled_movie_handler.db_connect')
    def test_scraped_movie_handler(self, db_connect_mock,
                                   add_item_to_database_mock,
                                   exist_func_mock):
        handler = CrawledMovieHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        data = {
            "title": "Your Name.",
            "current_cinema_count": 1
        }
        exist_func_mock.return_value = None
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].current_cinema_count, 1)

        exist_data = {
            "title": "Your Name.",
            "current_cinema_count": 3
        }
        exist_movie = Movie(**exist_data)
        exist_func_mock.return_value = exist_movie
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 2)
        expected_count = \
            data["current_cinema_count"] + exist_data["current_cinema_count"]
        args, kwargs = add_item_to_database_mock.call_args_list[1]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].current_cinema_count, expected_count)

    @patch('models.cinema.Cinema.get_cinema_if_exist')
    @patch('plugins.crawled_cinema_handler.add_item_to_database')
    @patch('plugins.crawled_cinema_handler.db_connect')
    def test_scraped_cinema_handler(self, db_connect_mock,
                                    add_item_to_database_mock,
                                    exist_func_mock):
        handler = CrawledCinemaHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        # test add brand new data
        proto_data = {
            "names": ["cinema_name_1"],
            "county": "test_county",
            "company": "test_company",
            "site": "test_site",
            "screens": {
                "screen1": "100",
                "screen2": "200",
            },
            "screen_count": 2,
            "total_seats": 300,
            "source": "test_source",
        }
        exist_func_mock.return_value = None
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, proto_data['total_seats'])
        self.assertEqual(args[1].source, proto_data['source'])

        # test cinema exists with more screens
        exist_data = deepcopy(proto_data)
        exist_data["screens"] = {
                "screen1": "100",
                "screen2": "200",
                "screen3": "300",
            }
        exist_data["screen_count"] = 3
        exist_data["total_seats"] = 600
        exist_data["source"] = "exist_source"
        exist_movie = Cinema(**exist_data)
        exist_func_mock.return_value = exist_movie
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 2)
        args, kwargs = add_item_to_database_mock.call_args_list[1]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, exist_data['total_seats'])
        self.assertEqual(args[1].source, exist_data['source'])

        # test cinema exists with less screens
        exist_data = deepcopy(proto_data)
        exist_data["screens"] = {
                "screen1": "100",
            }
        exist_data["screen_count"] = 1
        exist_data["total_seats"] = 100
        exist_data["source"] = "exist_source"
        exist_movie = Cinema(**exist_data)
        exist_func_mock.return_value = exist_movie
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 3)
        args, kwargs = add_item_to_database_mock.call_args_list[2]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, proto_data['total_seats'])
        self.assertEqual(args[1].source, proto_data['source'])

        # TODO test case for same source, no site with exist cinema
        # TODO test case for same source, site with exist cinema
