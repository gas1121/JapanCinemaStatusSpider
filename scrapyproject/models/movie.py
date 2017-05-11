from fuzzywuzzy import process
from sqlalchemy import Column, Integer, String
from scrapyproject.models import Session
from scrapyproject.models.models import DeclarativeBase


class Movie(DeclarativeBase):
    __tablename__ = "movie"

    id = Column(Integer, primary_key=True)
    title = Column('title', String, nullable=False)
    # cinema count for current week
    current_cinema_count = Column('current_cinema_count', Integer,
                                  default=0)

    @staticmethod
    def get_movie_if_exist(item):
        """
        Get movie if exists else return None.
        Judged by title
        """
        query = Session.query(Movie).filter(Movie.title == item.title)
        result = query.first()
        return result

    @staticmethod
    def get_by_title(title):
        """
        fuzzy search movie item from database
        """
        query = Session.query(Movie.title)
        result = query.all()
        title_list = [title for title, in result]
        result_title, ratio = process.extractOne(title, title_list)
        if ratio > 60:
            return result_title
        else:
            return None
