from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ArrowType
from sqlalchemy import and_
import arrow

from jcssutils import DeclarativeBase
from crawler.models import Session


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
    def from_item(item):
        item_dict = dict(item)
        # convert time str to Arrow object
        item_dict["start_time"] = arrow.get(item_dict["start_time"])
        if "end_time" in item_dict:
            item_dict["end_time"] = arrow.get(item_dict["end_time"])
        return Showing(**item_dict)

    @staticmethod
    def get_showing_if_exist(model_item):
        """
        Get showing if exists else return None.
        Judged by cinema site, screen and start time
        """
        # convert all time to utc timezone before compare
        start_time = model_item.start_time.to('utc')
        pre_start_time = start_time.shift(minutes=-1)
        post_start_time = start_time.shift(minutes=+1)
        query = Session.query(Showing).filter(and_(
            Showing.screen == model_item.screen,
            Showing.cinema_site == model_item.cinema_site,
            Showing.start_time > pre_start_time,
            Showing.start_time < post_start_time)).with_for_update()
        result = query.first()
        return result
