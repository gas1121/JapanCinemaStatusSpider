# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from scrapyproject.models import (Cinemas, Sessions, db_connect,
                                  drop_table_if_exist, create_table)
from scrapyproject.utils.spider_helper import (use_cinemas_database,
                                               use_sessions_database)


class DataBasePipeline(object):
    """
    pipeline to add item to database
    will keep exist data if spider has attribute 'keep_old_data'
    """
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
            if use_sessions_database(spider):
                drop_table_if_exist(engine, Sessions)
            elif use_cinemas_database(spider):
                drop_table_if_exist(engine, Cinemas)
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        """
        use cinema table if spider has attribute "use_cinemas_database"
        use session table if spider has attribute "use_sessions_database"
        a spider should not have both attributes
        """
        if use_cinemas_database(spider):
            return self.process_cinema_item(item, spider)
        elif use_sessions_database(spider):
            return self.process_session_item(item, spider)

    def process_cinema_item(self, item, spider):
        cinema = Cinemas(**item)
        exist_cinema = Cinemas.get_cinema_if_exist(cinema)
        if not exist_cinema:
            # if data do not exist in database, add it
            self.add_item_to_database(cinema)
        else:
            # otherwise check if it should be merged to exist record
            # merge strategy:
            # - if exist data is crawled from other source, only add names
            # and screens to exist data;
            # - if cinema do not have site url, item is treated as duplicate
            # and dropped;
            # - otherwise, merge all data
            if cinema.source != exist_cinema.source:
                # replace when new cinema data crawled more screens
                if cinema.screen_count > exist_cinema.screen_count:
                    exist_cinema.merge(
                        cinema, merge_method=Cinemas.MergeMethod.replace)
                else:
                    exist_cinema.merge(
                        cinema, merge_method=Cinemas.MergeMethod.info_only)
                self.add_item_to_database(exist_cinema)
            elif cinema.site:
                exist_cinema.merge(
                    cinema, merge_method=Cinemas.MergeMethod.update_count)
                self.add_item_to_database(exist_cinema)
        return item

    def process_session_item(self, item, spider):
        session = Sessions(**item)
        # if data do not exist in database, add it
        if not Sessions.is_session_exist(session):
            self.add_item_to_database(session)
        return item

    def add_item_to_database(self, db_item):
        session = self.Session()
        try:
            db_item = session.merge(db_item)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
