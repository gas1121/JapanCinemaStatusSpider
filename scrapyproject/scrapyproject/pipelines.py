# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from scrapyproject.models import (Cinemas, Sessions, db_connect,
                                  drop_table_if_exist, create_cinemas_table,
                                  is_session_exist)


class DataBasePipeline(object):
    def __init__(self, database):
        self.database = database

    @classmethod
    def from_crawler(cls, crawler):
        return cls(database=crawler.settings.get('DATABASE'))

    def open_spider(self, spider):
        self.keep_old_data = (
            True if hasattr(spider, 'keep_old_data') else False)
        engine = db_connect()
        if not self.keep_old_data:
            # drop data
            if spider.name == "toho" or spider.name == "toho_v2":
                drop_table_if_exist(engine, Sessions)
            elif spider.name == "toho_cinema":
                drop_table_if_exist(engine, Cinemas)
        create_cinemas_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        if (spider.name == "toho_cinema" or spider.name == "toho"
                or spider.name == "toho_v2"):
            db_item = (Cinemas(**item) if spider.name == "toho_cinema"
                       else Sessions(**item))
            # if spider is toho or toho_v2 and keep old data,
            # check if data exists first
            if ((spider.name == "toho" or spider.name == "toho_v2") and
                    is_session_exist(db_item)):
                    return item
            # save cinema info to database
            session = self.Session()
            try:
                session.add(db_item)
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()
        return item
