from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from scrapyproject import settings


DeclarativeBase = declarative_base()


def create_cinemas_table(engine):
    DeclarativeBase.metadata.create_all(engine)


def db_connect():
    """
    connect to database described in settings
    if database is not yet exist,will create first
    """
    engine = create_engine(URL(**settings.DATABASE))
    if not database_exists(engine.url):
        create_database(engine.url)
    return engine


class Cinemas(DeclarativeBase):
    __tablename__ = "cinemas"

    id = Column(Integer, primary_key=True)
    name = Column('name', String, unique=True)
    screens = Column('screens', JSONB)
