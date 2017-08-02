import unittest
import os

from sqlalchemy import Column, Integer
from sqlalchemy.engine.url import URL
from sqlalchemy_utils import drop_database
from models import (DeclarativeBase, create_table,
                    drop_table_if_exist, db_connect)


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


if __name__ == '__main__':
    unittest.main()
