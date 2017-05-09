from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy_utils import ArrowType
from sqlalchemy import and_
from scrapyproject.models.models import DeclarativeBase, db_connect


class ShowingOverwiew(DeclarativeBase):
    __tablename__ = "showing_overview"

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movie.id"))
    movie = relationship("Movie")
    cinema_id = Column(Integer, ForeignKey("showing.id"))
    cinema = relationship("Showing")
    date = Column('date', ArrowType, nullable=False)
    showing_count = Column('showing_count', Integer, default=0,
                           nullable=False)

    record_time = Column('record_time', ArrowType, nullable=False)

    @staticmethod
    def get_showing_overview_if_exist(item):
        """
        Get showing overview if exists else return None.
        Judged by movie, cinema and date
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        # date should be 00:00 utc
        date = item.start_time.to('utc')
        pre_date = date.shift(minutes=-1)
        post_date = date.shift(minutes=+1)
        query = session.query(ShowingOverwiew).filter(and_(
            ShowingOverwiew.movie_id = item.movie_id,
            ShowingOverwiew.cinema_id = item.cinema_id,
            ShowingOverwiew.date > pre_date,
            ShowingOverwiew.date < post_date))
        result = query.first()
        session.close()
        return result
        # TODO
