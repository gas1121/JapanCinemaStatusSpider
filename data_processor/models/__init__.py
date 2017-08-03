import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database


DATABASE = {
    'drivername': 'postgres',
    'host': 'postgres',
    'port': '5432',
    'username': os.getenv('POSTGRES_USER', 'test'),
    'password': os.getenv('POSTGRES_PASSWORD', 'test'),
    'database': os.getenv('POSTGRES_DB', 'test')
}

DeclarativeBase = declarative_base()


def create_table(engine):
    """Create tables from given engine
    """
    con = engine.connect()
    trans = con.begin()
    DeclarativeBase.metadata.create_all(con)
    trans.commit()


def drop_table_if_exist(engine, TableClass):
    """Drop target table if exist
    """
    if engine.dialect.has_table(engine, TableClass.__table__):
        con = engine.connect()
        trans = con.begin()
        TableClass.__table__.drop(con)
        trans.commit()


def db_connect(database=DATABASE):
    """Get a sqlalchemy engine connected to targe database.
    If database is not yet exist, will create first
    """
    engine = create_engine(URL(**database))
    if not database_exists(engine.url):
        create_database(engine.url)
    return engine


def add_item_to_database(session, db_item):
    """Add a item to database with given session
    """
    try:
        db_item = session.merge(db_item)
        session.commit()
    except:
        session.rollback()
        raise


# global session for project
Session = scoped_session(sessionmaker(bind=db_connect()))
