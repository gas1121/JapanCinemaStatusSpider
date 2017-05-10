from fuzzywuzzy import process
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from scrapyproject.models.models import DeclarativeBase, db_connect


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
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Movie).filter(Movie.title == item.title)
        result = query.first()
        session.close()
        return result

    @staticmethod
    def get_by_title(title):
        """
        fuzzy search movie item from database
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Movie.title)
        result = query.all()
        session.close()
        title_list = [title for title, in result]
        result_title, ratio = process.extractOne(title, title_list)
        if ratio > 60:
            return result_title
        else:
            return None
