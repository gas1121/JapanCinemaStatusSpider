from datetime import timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from scrapyproject import settings


DeclarativeBase = declarative_base()


def create_cinemas_table(engine):
    DeclarativeBase.metadata.create_all(engine)


def drop_table_if_exist(engine, TableClass):
    if engine.dialect.has_table(engine, TableClass.__table__):
        TableClass.__table__.drop(engine)


def db_connect():
    """
    connect to database described in settings
    if database is not yet exist,will create first
    """
    engine = create_engine(URL(**settings.DATABASE))
    if not database_exists(engine.url):
        create_database(engine.url)
    return engine


def query_cinema_by_name(cinema_name):
    engine = db_connect()
    session = sessionmaker(bind=engine)()
    query = session.query(Cinemas).filter(
        Cinemas.name == cinema_name
    )
    cinema = query.first()
    session.close()
    return cinema


def is_session_exist(item):
    """
    check if session exist in database by cinema_name, screen and start time
    """
    engine = db_connect()
    session = sessionmaker(bind=engine)()
    pre_start_time = item.start_time - timedelta(minutes=1)
    post_start_time = item.start_time + timedelta(minutes=1)
    query = session.query(exists().where(
        Sessions.screen == item.screen).where(
            Sessions.cinema_name == item.cinema_name).where(
                Sessions.start_time > pre_start_time).where(
                    Sessions.start_time < post_start_time))
    result = query.scalar()
    session.close()
    return result


def is_cinema_exist(item):
    """
    check if cinema exist in database by name and county
    """
    engine = db_connect()
    session = sessionmaker(bind=engine)()
    query = session.query(exists().where(
        Cinemas.name == item.name)).where(Cinemas.county == item.county)
    result = query.scalar()
    session.close()
    return result


class Cinemas(DeclarativeBase):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    name = Column('name', String, unique=True)
    county = Column('county', String)
    company = Column('county', String)
    screens = Column('screens', JSONB)


class Sessions(DeclarativeBase):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    title = Column('title', String)
    title_en = Column('title_en', String)
    start_time = Column('start_time', DateTime)
    end_time = Column('end_time', DateTime)
    cinema_name = Column('cinema_name', String)
    screen = Column('screen', String)
    book_status = Column('book_status', String)
    book_seat_count = Column('book_seat_count', Integer, default=0)
    total_seat_count = Column('total_seat_count', Integer, default=0)
    record_time = Column('record_time', DateTime)
