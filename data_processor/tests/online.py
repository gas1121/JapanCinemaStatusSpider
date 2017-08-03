import unittest
from mock import MagicMock, patch
import os
import json

from sqlalchemy import Column, Integer, String
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import drop_database
from kafka_monitor import KafkaMonitor
from scutils.method_timer import MethodTimer

from models import (DeclarativeBase, create_table,
                    drop_table_if_exist, db_connect, add_item_to_database)
from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler
from plugins.scraped_movie_handler import ScrapedMovieHandler


class DatabaseMixin(object):
    def setUp(self):
        self.database = {
            'drivername': 'postgres',
            'host': 'postgres',
            'port': '5432',
            'username': os.getenv('POSTGRES_USER', 'test'),
            'password': os.getenv('POSTGRES_PASSWORD', 'test'),
            'database': 'test'
        }
        self.url = URL(**self.database)

    def tearDown(self):
        drop_database(self.url)


class TestTable(DeclarativeBase):
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)
    data = Column('data', String)


class TestModels(DatabaseMixin, unittest.TestCase):
    def test_db_connect(self):
        engine = db_connect(self.database)
        self.assertEqual(engine.name, 'postgresql')

    def test_create_table(self):
        engine = db_connect(self.database)
        self.assertFalse(engine.dialect.has_table(
            engine, TestTable.__tablename__))
        create_table(engine)
        self.assertTrue(engine.dialect.has_table(
            engine, TestTable.__tablename__))

    def test_drop_table_if_exist(self):
        engine = db_connect(self.database)
        self.assertFalse(engine.dialect.has_table(
            engine, TestTable.__tablename__))
        drop_table_if_exist(engine, TestTable)
        self.assertFalse(engine.dialect.has_table(
            engine, TestTable.__tablename__))

        create_table(engine)
        drop_table_if_exist(engine, TestTable)
        self.assertFalse(engine.dialect.has_table(
            engine, TestTable.__tablename__))

    def test_add_item_to_database(self):
        engine = db_connect(self.database)
        test_session = sessionmaker(bind=engine)()
        self.assertFalse(engine.dialect.has_table(
            engine, TestTable.__tablename__))
        create_table(engine)
        self.assertTrue(engine.dialect.has_table(
            engine, TestTable.__tablename__))
        item = TestTable()
        item.data = "test data"
        add_item_to_database(test_session, item)
        result = test_session.query(TestTable).all()
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0].data, "test data")


class TestDbManageHandler(DatabaseMixin, unittest.TestCase):
    @patch('plugins.dbmanage_handler.db_connect')
    def test_handle(self, db_connect_mock):
        handler = DbManageHandler()
        handler.logger = MagicMock()
        handler.setup(MagicMock())
        handler.engine = db_connect(self.database)
        self.assertEqual(handler.engine.name, 'postgresql')
        data = {
            "action": "clear",
            "target": "all"
        }
        self.assertFalse(handler.engine.dialect.has_table(
            handler.engine, Cinema.__table__))
        self.assertFalse(handler.engine.dialect.has_table(
            handler.engine, Movie.__table__))
        self.assertFalse(handler.engine.dialect.has_table(
            handler.engine, ShowingBooking.__table__))
        self.assertFalse(handler.engine.dialect.has_table(
            handler.engine, Showing.__table__))
        handler.handle(data)
        self.assertTrue(handler.engine.dialect.has_table(
            handler.engine, Cinema.__table__))
        self.assertTrue(handler.engine.dialect.has_table(
            handler.engine, Movie.__table__))
        self.assertTrue(handler.engine.dialect.has_table(
            handler.engine, ShowingBooking.__table__))
        self.assertTrue(handler.engine.dialect.has_table(
            handler.engine, Showing.__table__))


class TestScrapedMovieHandler(DatabaseMixin, unittest.TestCase):
    def test_handle(self):
        engine = db_connect(self.database)
        with patch('plugins.scraped_movie_handler.Session', scoped_session(
                        sessionmaker(bind=engine))) as Session_mock:
            handler = ScrapedMovieHandler()
            handler.logger = MagicMock()
            handler.setup(MagicMock())
            handler.engine = engine
            self.assertEqual(handler.engine.name, 'postgresql')
            data = {
                "title": "Your Name.",
                "current_cinema_count": 2
            }
            create_table(handler.engine)
            self.assertTrue(handler.engine.dialect.has_table(
                handler.engine, Movie.__table__))
            result = Session_mock.query(Movie).all()
            self.assertFalse(result)
            handler.handle(data)
            result = Session_mock.query(Movie).all()
            self.assertEquals(len(result), 1)
            self.assertEquals(result[0].title, "Your Name.")
            self.assertEquals(result[0].current_cinema_count, 2)


# setup custom class to handle our requests
class CustomHandler(MagicMock):
    # use dbmanage handler's schema just for test
    schema = "dbmanage_schema.json"

    def handle(self, dict):
        pass


class TestKafkaMonitor(unittest.TestCase):
    def setUp(self):
        self.kafka_monitor = KafkaMonitor("localsettings.py")
        new_settings = self.kafka_monitor.wrapper.load("localsettings.py")
        new_settings['KAFKA_INCOMING_TOPIC'] = "jcss.incoming_test"
        new_settings['KAFKA_CONSUMER_TIMEOUT'] = 5000
        new_settings['STATS_TOTAL'] = False
        new_settings['STATS_PLUGINS'] = False
        new_settings['PLUGINS'] = {
            'plugins.dbmanage_handler.DbManageHandler': None,
            'tests.online.CustomHandler': 100,
        }

        self.kafka_monitor.wrapper.load = MagicMock(return_value=new_settings)
        self.kafka_monitor.setup()

        @MethodTimer.timeout(10, False)
        def timer():
            self.kafka_monitor._setup_kafka()
            return True

        retval = timer()
        if not retval:
            self.fail("Unable to connect to Kafka")
        self.kafka_monitor._load_plugins()
        self.kafka_monitor._setup_stats()
        self.assertTrue(100 in self.kafka_monitor.plugins_dict)
        self.assertTrue(isinstance(
            self.kafka_monitor.plugins_dict[100]['instance'], CustomHandler))

    def test_feed(self):
        json_req = "{\"action\":\"init\",\"target\":\"all\"}"
        parsed = json.loads(json_req)
        # ensure the group id is present so we pick up the 1st message
        self.kafka_monitor._process_messages()
        self.kafka_monitor.feed(parsed)

    def test_run(self):
        handler = self.kafka_monitor.plugins_dict[100]['instance']
        handler.handle = MagicMock()
        self.kafka_monitor._process_messages()
        handler.handle.assert_called_once()

    def tearDown(self):
        self.kafka_monitor.close()


if __name__ == '__main__':
    unittest.main()
