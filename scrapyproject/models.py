from datetime import timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from scrapyproject import settings


DeclarativeBase = declarative_base()


def create_table(engine):
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
        Cinemas.names.contains(cinema_name)
    )
    cinema = query.first()
    session.close()
    return cinema


def is_session_exist(item):
    """
    check if session exist in database by cinema_name, screen and start time
    """
    # TODO
    return False
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
    check if cinema exists in database by its official site url if exists,
    otherwise by cinema's screen_count, total_seats and area

    edge cases like redirected url and alias url should be handle before
    calling this function
    """
    engine = db_connect()
    session = sessionmaker(bind=engine)()
    if item.site:
        query = session.query(exists().where(Cinemas.site == item.site))
    else:
        # as only a very few  number of cinemas do not have official site,
        # it's currently safe to only use screen_count and total_seats to
        # identify such a cinema
        query = session.query(exists().where(
                Cinemas.screen_count == item.screen_count
            ).where(
                Cinemas.total_seats == item.total_seats
            ))
    result = query.scalar()
    session.close()
    return result


class Cinemas(DeclarativeBase):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    # name may differ depends on crawled site, so we collect all names
    # in order to make query easier.
    names = Column('names', ARRAY(String), nullable=False)
    county = Column('county', String, nullable=False)
    company = Column('company', String)
    site = Column('site', String)
    # screens are handled as same as names
    screens = Column('screens', JSONB, nullable=False)
    # as screens may contain multiple versions of single screen,
    # we use next two column to help identify a cinema
    screen_count = Column('screen_count', Integer, nullable=False)
    total_seats = Column('total_seats', Integer, nullable=False)


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
