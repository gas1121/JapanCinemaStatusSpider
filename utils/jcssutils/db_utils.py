"""
utils for database related operations
"""
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database


DeclarativeBase = declarative_base()


def create_table(engine):
    """Create tables from given engine
    """
    DeclarativeBase.metadata.create_all(engine)


def drop_table_if_exist(engine, TableClass):
    """Drop target table if exist
    """
    if engine.dialect.has_table(engine, TableClass.__table__):
        TableClass.__table__.drop(engine)


def db_connect(database):
    """Get a sqlalchemy engine connected to targe database.
    If database is not yet exist, will create first

    @param database: a dict contains settings for database
    """
    engine = create_engine(URL(**database))
    if not database_exists(engine.url):
        create_database(engine.url)
    return engine
