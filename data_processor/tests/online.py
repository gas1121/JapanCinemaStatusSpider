import unittest
from mock import MagicMock, patch
import os

from sqlalchemy import Column, Integer
from sqlalchemy.engine.url import URL
from sqlalchemy_utils import drop_database
from models import (DeclarativeBase, create_table,
                    drop_table_if_exist, db_connect)
from models.cinema import Cinema
from models.movie import Movie
from models.showing import Showing
from models.showing_booking import ShowingBooking
from plugins.dbmanage_handler import DbManageHandler


class TestTable(DeclarativeBase):
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True)


class TestModels(unittest.TestCase):
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

    def tearDown(self):
        drop_database(self.url)


class TestDbManageHandler(unittest.TestCase):
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

    def tearDown(self):
        drop_database(self.url)


if __name__ == '__main__':
    unittest.main()
