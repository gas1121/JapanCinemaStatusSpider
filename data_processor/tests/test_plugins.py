import unittest
from mock import MagicMock, patch, call
from copy import deepcopy

import arrow

from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler
from plugins.crawled_movie_handler import CrawledMovieHandler
from plugins.crawled_cinema_handler import CrawledCinemaHandler
from plugins.crawled_showing_handler import CrawledShowingHandler
from plugins.crawled_showing_booking_handler import CrawledShowingBookingHandler


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
        add_item_to_database_mock.reset_mock()

        exist_data = {
            "title": "Your Name.",
            "current_cinema_count": 3
        }
        exist_movie = Movie(**exist_data)
        exist_func_mock.return_value = exist_movie
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        expected_count = \
            data["current_cinema_count"] + exist_data["current_cinema_count"]
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].current_cinema_count, expected_count)
        add_item_to_database_mock.reset_mock()

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
        add_item_to_database_mock.reset_mock()

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
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, exist_data['total_seats'])
        self.assertEqual(args[1].source, exist_data['source'])
        add_item_to_database_mock.reset_mock()

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
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, proto_data['total_seats'])
        self.assertEqual(args[1].source, proto_data['source'])
        add_item_to_database_mock.reset_mock()

        # same source, no site with exist cinema
        exist_data = deepcopy(proto_data)
        exist_data["screens"] = {
                "screen1": "100",
            }
        exist_data["site"] = None
        exist_data["screen_count"] = 1
        exist_data["total_seats"] = 100
        exist_movie = Cinema(**exist_data)
        exist_func_mock.return_value = exist_movie
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].total_seats, proto_data['total_seats'])
        self.assertEqual(args[1].source, proto_data['source'])
        add_item_to_database_mock.reset_mock()

        # same source, site with exist cinema
        exist_data = deepcopy(proto_data)
        exist_data["screens"] = {
                "screen4": "400",
            }
        exist_data["screen_count"] = 1
        exist_data["total_seats"] = 400
        exist_movie = Cinema(**exist_data)
        exist_func_mock.return_value = exist_movie
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        expect_total_seats = exist_data["total_seats"] +\
            proto_data['total_seats']
        self.assertEqual(args[1].total_seats, expect_total_seats)

    @patch('models.cinema.Cinema.get_screen_seat_count')
    @patch('models.movie.Movie.get_by_title')
    @patch('models.showing.Showing.get_showing_if_exist')
    @patch('plugins.crawled_showing_handler.add_item_to_database')
    @patch('plugins.crawled_showing_handler.db_connect')
    def test_scraped_showing_handler(self, db_connect_mock,
                                     add_item_to_database_mock,
                                     exist_func_mock,
                                     get_by_title_mock,
                                     get_screen_seat_count_mock):
        handler = CrawledShowingHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        # test add brand new data
        proto_data = {
            "title": "Your Name.",
            "title_en": "Your Name.",
            "start_time": arrow.get("201608271200", 'YYYYMMDDhhmm').format(),
            "end_time": arrow.get("201608271400", 'YYYYMMDDhhmm').format(),
            "cinema_name": "test_cinema",
            "cinema_site": "test_site",
            "screen": "test_screen",
            "seat_type": "FreeSeat",
            "source": "test_source",
        }
        exist_func_mock.return_value = None
        get_by_title_mock.return_value = "Your Name."
        get_screen_seat_count_mock.return_value = 300
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].screen, proto_data['screen'])
        self.assertEqual(args[1].real_title, "Your Name.")
        self.assertEqual(args[1].total_seat_count, 300)

        # test cinema exists with more screens
        session = MagicMock()
        exist_showing = Showing.from_item(session, proto_data)
        exist_func_mock.return_value = exist_showing
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)

    @patch('models.cinema.Cinema.get_screen_seat_count')
    @patch('models.movie.Movie.get_by_title')
    @patch('models.showing.Showing.get_showing_if_exist')
    @patch('plugins.crawled_showing_booking_handler.add_item_to_database')
    @patch('plugins.crawled_showing_booking_handler.db_connect')
    def test_scraped_showing_booking_handler(self, db_connect_mock,
                                             add_item_to_database_mock,
                                             exist_func_mock,
                                             get_by_title_mock,
                                             get_screen_seat_count_mock):
        handler = CrawledShowingBookingHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        # test add brand new data
        proto_showing_data = {
            "title": "Your Name.",
            "title_en": "Your Name.",
            "start_time": arrow.get("201608271200", 'YYYYMMDDhhmm').format(),
            "end_time": arrow.get("201608271400", 'YYYYMMDDhhmm').format(),
            "cinema_name": "test_cinema",
            "cinema_site": "test_site",
            "screen": "test_screen",
            "seat_type": "FreeSeat",
            "source": "test_source",
        }
        proto_data = {
            "showing": proto_showing_data,
            "book_status": "PlentyLeft",
            "book_seat_count": 55,
            "minutes_before": 60,
            "record_time": arrow.get("201608271100", 'YYYYMMDDhhmm').format(),
        }
        exist_func_mock.return_value = None
        get_by_title_mock.return_value = "Your Name."
        get_screen_seat_count_mock.return_value = 300
        data = deepcopy(proto_data)
        handler.handle(data)
        self.assertEqual(add_item_to_database_mock.call_count, 1)
        args, kwargs = add_item_to_database_mock.call_args_list[0]
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1].minutes_before, proto_data['minutes_before'])
        self.assertEqual(args[1].showing.real_title, "Your Name.")
        self.assertEqual(args[1].showing.total_seat_count, 300)
