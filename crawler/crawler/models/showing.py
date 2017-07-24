from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ArrowType
from sqlalchemy import and_
from crawler.models import Session
from crawler.models.models import DeclarativeBase


class Showing(DeclarativeBase):
    __tablename__ = "showing"

    id = Column(Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    title_en = Column('title_en', String)
    real_title = Column('real_title', String)
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
    def get_showing_if_exist(item):
        """
        Get showing if exists else return None.
        Judged by cinema site, screen and start time
        """
        # convert all time to utc timezone before compare
        start_time = item.start_time.to('utc')
        pre_start_time = start_time.shift(minutes=-1)
        post_start_time = start_time.shift(minutes=+1)
        query = Session.query(Showing).filter(and_(
            Showing.screen == item.screen,
            Showing.cinema_site == item.cinema_site,
            Showing.start_time > pre_start_time,
            Showing.start_time < post_start_time)).with_for_update()
        result = query.first()
        return result
