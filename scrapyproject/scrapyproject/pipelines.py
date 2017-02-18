# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from scrapyproject.models import Cinemas, db_connect, create_cinemas_table


class DataBasePipeline(object):
    def __init__(self, database):
        self.database = database

    @classmethod
    def from_crawler(cls, crawler):
        return cls(database=crawler.settings.get('DATABASE'))

    def open_spider(self, spider):
        engine = db_connect()
        create_cinemas_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        if spider.name == "toho_cinema":
            # save cinema info to database
            session = self.Session()
            cinema = Cinemas(**item)
            try:
                session.add(cinema)
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()
        return item
