from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database, ArrowType
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists, and_, or_, cast
from scrapyproject import settings


DeclarativeBase = declarative_base()


def create_table(engine):
    DeclarativeBase.metadata.create_all(engine)


def drop_table_if_exist(engine, TableClass):
    if engine.dialect.has_table(engine, TableClass.__table__):
        TableClass.__table__.drop(engine)


def db_connect():
    """
    Connect to database described in settings
    if database is not yet exist,will create first
    """
    engine = create_engine(URL(**settings.DATABASE))
    if not database_exists(engine.url):
        create_database(engine.url)
    return engine


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
    # site that data mainly crawled from
    source = Column('source', String, nullable=False)

    @staticmethod
    def get_cinema_if_exist(item):
        """
        Get cinema if it already exists in database, otherwise return None

        As data crawled from those sites often differs between each other,
        we have several rules to use to find exist cinema:
        - first of all, same "county", then:
        - have "site", same "site";
        - have name in "names", same name in "names";
        Some cinemas may be treated as different cinemas when crawled from
        different site but we will leave them there now.
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Cinemas).filter(and_(
            Cinemas.county == item.county, or_(
                and_(item.site is not None, Cinemas.site == item.site),
                and_(item.names is not None, Cinemas.names.overlap(
                    cast(item.names, ARRAY(String))))
            )))
        result = query.first()
        session.close()
        return result

    @staticmethod
    def get_by_name(cinema_name):
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Cinemas).filter(
            Cinemas.names.any(cinema_name)
        )
        cinema = query.first()
        session.close()
        return cinema

    class MergeMethod(Enum):
        info_only = 1  # update names and screens only
        update_count = 2  # also update screen count and total seat number
        replace = 3  # replace all data

    def merge(self, new_cinema, merge_method):
        """
        merge data from new crawled cinema data depends on strategy
        """
        if merge_method == self.MergeMethod.info_only:
            self.names.extend(x for x in new_cinema.names if
                              x not in self.names)
            new_cinema.screens.update(self.screens)
            self.screens = new_cinema.screens
        elif merge_method == self.MergeMethod.update_count:
            self.names.extend(x for x in new_cinema.names if
                              x not in self.names)
            for new_screen in new_cinema.screens:
                if new_screen not in self.screens:
                    curr_seat_count = int(new_cinema.screens[new_screen])
                    self.screens[new_screen] = curr_seat_count
                    self.screen_count += 1
                    self.total_seats += curr_seat_count
        else:
            new_cinema.id = self.id
            self = new_cinema


class Sessions(DeclarativeBase):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    title_en = Column('title_en', String)
    start_time = Column('start_time', ArrowType, nullable=False)
    end_time = Column('end_time', ArrowType, nullable=False)
    cinema_name = Column('cinema_name', String, nullable=False)
    cinema_site = Column('cinema_site', String, nullable=False)
    screen = Column('screen', String, nullable=False)
    book_status = Column('book_status', String, nullable=False)
    book_seat_count = Column('book_seat_count', Integer, default=0,
                             nullable=False)
    total_seat_count = Column('total_seat_count', Integer, default=0,
                              nullable=False)
    record_time = Column('record_time', ArrowType, nullable=False)
    # site that data crawled from
    source = Column('source', String, nullable=False)

    @staticmethod
    def is_session_exist(item):
        """
        Check if session exist by cinema site, screen and start time
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        pre_start_time = item.start_time.shift(minutes=-1)
        post_start_time = item.start_time.shift(minutes=+1)
        query = session.query(exists().where(
            Sessions.screen == item.screen).where(
                Sessions.cinema_site == item.cinema_site).where(
                    Sessions.start_time > pre_start_time).where(
                        Sessions.start_time < post_start_time))
        result = query.scalar()
        session.close()
        return result
