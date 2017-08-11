from sqlalchemy import Column, Integer, String
from sqlalchemy_utils import ArrowType
from sqlalchemy import and_
import arrow

from models import DeclarativeBase
from models.movie import Movie
from models.cinema import Cinema


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
    def from_item(session, item):
        item_dict = dict(item)
        # convert time str to Arrow object
        item_dict["start_time"] = arrow.get(item_dict["start_time"])
        if "end_time" in item_dict:
            item_dict["end_time"] = arrow.get(item_dict["end_time"])
        showing = Showing(**item_dict)
        # query real title in database
        if not showing.real_title:
            showing.real_title = Movie.get_by_title(session, showing.title)
        # query total_seat_count in database
        if not showing.total_seat_count:
            showing.total_seat_count = Cinema.get_screen_seat_count(
                session,
                cinema_name=showing.cinema_name,
                cinema_site=showing.cinema_site,
                screen=showing.screen)
        return showing

    @staticmethod
    def get_showing_if_exist(session, model_item):
        """
        Get showing if exists else return None.
        Judged by cinema site, screen and start time
        """
        # convert all time to utc timezone before compare
        start_time = model_item.start_time.to('utc')
        pre_start_time = start_time.shift(minutes=-1)
        post_start_time = start_time.shift(minutes=+1)
        query = session.query(Showing).filter(and_(
            Showing.screen == model_item.screen,
            Showing.cinema_site == model_item.cinema_site,
            Showing.start_time > pre_start_time,
            Showing.start_time < post_start_time)).with_for_update()
        result = query.first()
        return result
