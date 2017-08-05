import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database


# make sure database is same as username so we can connect the database
# created by postgres docker container when start up
DATABASE = {
    'drivername': 'postgres',
    'host': 'postgres',
    'port': '5432',
    'username': os.getenv('POSTGRES_USER', 'testdefault'),
    'password': os.getenv('POSTGRES_PASSWORD', 'testdefault'),
    'database': os.getenv('POSTGRES_DB', 'testdefault'),
}

DeclarativeBase = declarative_base()


def create_table(engine):
    """Create tables from given engine
    """
    con = engine.connect()
    trans = con.begin()
    DeclarativeBase.metadata.create_all(con)
    trans.commit()
    con.close()


def drop_table_if_exist(engine, TableClass):
    """Drop target table if exist
    """
    if engine.dialect.has_table(engine, TableClass.__table__):
        con = engine.connect()
        trans = con.begin()
        TableClass.__table__.drop(con)
        trans.commit()
        con.close()


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
