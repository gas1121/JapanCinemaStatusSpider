from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ArrowType
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exists
from scrapyproject.models.models import DeclarativeBase, db_connect


class Showing(DeclarativeBase):
    __tablename__ = "showing"

    id = Column(Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    title_en = Column('title_en', String)
    start_time = Column('start_time', ArrowType, nullable=False)
    end_time = Column('end_time', ArrowType)
    cinema_name = Column('cinema_name', String, nullable=False)
    cinema_site = Column('cinema_site', String, nullable=False)
    screen = Column('screen', String, nullable=False)
    seat_type = Column('seat_type', String, nullable=False)
    total_seat_count = Column('total_seat_count', Integer, default=0,
                              nullable=False)
    # site that data crawled from
    source = Column('source', String, nullable=False)

    @staticmethod
    def is_showing_exist(item):
        """
        Check if showing exist by cinema site, screen and start time
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        pre_start_time = item.start_time.shift(minutes=-1)
        post_start_time = item.start_time.shift(minutes=+1)
        query = session.query(exists().where(
            Showing.screen == item.screen).where(
                Showing.cinema_site == item.cinema_site).where(
                    Showing.start_time > pre_start_time).where(
                        Showing.start_time < post_start_time))
        result = query.scalar()
        session.close()
        return result
