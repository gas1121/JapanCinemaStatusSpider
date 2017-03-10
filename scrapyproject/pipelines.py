# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from sqlalchemy.orm import sessionmaker
from scrapyproject.models import (Cinemas, Showings, db_connect,
                                  drop_table_if_exist, create_table)
from scrapyproject.utils.spider_helper import (use_cinemas_database,
                                               use_showings_database)


class DataBasePipeline(object):
    """
    pipeline to add item to database
    will keep exist data if spider has attribute 'keep_old_data'
    """
    def __init__(self, database):
        self.database = database
        self.sold_out_showings = []
        # screen seat cache for counting sold out showing's data
        self.screen_cache = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls(database=crawler.settings.get('DATABASE'))

    def open_spider(self, spider):
        self.keep_old_data = (
            True if hasattr(spider, 'keep_old_data') else False)
        engine = db_connect()
        if not self.keep_old_data:
            # drop data
            if use_showings_database(spider):
                drop_table_if_exist(engine, Showings)
            elif use_cinemas_database(spider):
                drop_table_if_exist(engine, Cinemas)
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def close_spider(self, spider):
        # For showing spider, sold out showing may exist, so we need
        # to fix data for these showings.
        if use_showings_database(spider) and self.sold_out_showings:
            for showing in self.sold_out_showings:
                cinema_name = showing.cinema_name
                screen = showing.screen
                if (cinema_name in self.screen_cache and
                        screen in self.screen_cache[cinema_name]):
                    showing.book_seat_count = self.screen_cache[
                        cinema_name][screen]
                    showing.total_seat_count = self.screen_cache[
                        cinema_name][screen]
                else:
                    cinema = Cinemas.get_by_name(showing.cinema_name)
                    if cinema and screen in cinema.screens:
                        showing.book_seat_count = cinema.screens[screen]
                        showing.total_seat_count = cinema.screens[screen]
                self.add_item_to_database(showing)

    def process_item(self, item, spider):
        """
        use cinema table if spider has attribute "use_cinemas_database"
        use showing table if spider has attribute "use_showings_database"
        a spider should not have both attributes
        """
        if use_cinemas_database(spider):
            return self.process_cinema_item(item, spider)
        elif use_showings_database(spider):
            return self.process_showing_item(item, spider)

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

    def process_showing_item(self, item, spider):
        showing = Showings(**item)
        # sold out item will pass by now and handle when spider finish
        if item['book_status'] == 'SoldOut':
            self.sold_out_showings.append(showing)
            return item
        # cache screen data for later use
        cinema_name = showing.cinema_name
        if cinema_name not in self.screen_cache:
            self.screen_cache[cinema_name] = {}
        if showing.screen not in self.screen_cache[cinema_name]:
            self.screen_cache[cinema_name][
                showing.screen] = showing.total_seat_count

        # if data do not exist in database, add it
        if not Showings.is_showing_exist(showing):
            self.add_item_to_database(showing)
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
