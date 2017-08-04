from kafka_monitor_plugins.base_handler import BaseHandler

from models import db_connect, add_item_to_database, Session
from models.movie import Movie


class CrawledMovieHandler(BaseHandler):
    schema = "crawled_movie_schema.json"

    def setup(self, settings):
        """
        Setup db connection
        """
        self.engine = db_connect()
        self.logger.debug("Connected to Database in {}".format(
            self.__class__.__name__))

    def handle(self, dict):
        """
        Processes a vaild database manage request

        @param dict: a valid dictionary object
        """
        # remove 'ts' item in input dict
        movie_dict = {k: v for k, v in dict.items() if k != 'ts'}
        movie = Movie(**movie_dict)
        exist_movie = Movie.get_movie_if_exist(Session, movie)
        if exist_movie:
            # if movie exist in database, sum cinema count
            exist_movie.current_cinema_count += movie.current_cinema_count
            movie = exist_movie
        try:
            add_item_to_database(Session, movie)
            self.logger.info('Movie added to database', extra=dict)
        except:
            self.logger.info('Movie failed add to database', extra=dict)
