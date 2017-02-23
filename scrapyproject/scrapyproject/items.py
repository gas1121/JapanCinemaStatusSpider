# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import unicodedata
import scrapy


special_screen = {
    "NICHIGEKI-1": "日劇1",
    "NICHIGEKI-2": "日劇2",
    "NICHIGEKI-3": "日劇3",
    "SCALAZA": "スカラ座",
    "MIYUKIZA": "みゆき座",
    "CHANTER-1": "SCREEN1",
    "CHANTER-2": "SCREEN2",
    "CHANTER-3": "SCREEN3"
}


def standardize_cinema_name(cinema_name):
    """
    standardize cinema name
    """
    return standardize_name(cinema_name)


def is_screen_name_special(screen_name):
    """
    check if given screen name is not same with screen name on cinemas table
    """
    return (screen_name in special_screen)


def convert_special_screen_name(screen_name):
    """
    convert special screen name to which is in cinemas table
    """
    if screen_name in special_screen:
        return special_screen[screen_name]
    else:
        return screen_name


def standardize_screen_name(screen_name):
    """
    standardize screen name
    """
    return standardize_name(screen_name)


def standardize_name(name):
    """
    remove all spaces, normalize full width characters to double width
    """
    name = unicodedata.normalize('NFKC', name)
    name = name.replace(' ', '')
    return name


class Cinema(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field()
    area = scrapy.Field()
    area_en = scrapy.Field()
    county = scrapy.Field()
    county_en = scrapy.Field()
    screens = scrapy.Field()


class Session(scrapy.Item):
    title = scrapy.Field()
    title_en = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    cinema_name = scrapy.Field()
    screen = scrapy.Field()
    book_status = scrapy.Field()
    book_seat_count = scrapy.Field()
    total_seat_count = scrapy.Field()
    record_time = scrapy.Field()
