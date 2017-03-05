# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import re
import unicodedata
import scrapy


special_cinema = {
    'TOHOシネマズシャンテ': {
        r'SCREEN': r'CHANTER-'
    },
    'TOHOシネマズスカラ座・みゆき座': {
        r'^スカラ座$': r'SCALAZA',
        r'^みゆき座$': r'MIYUKIZA'
    },
    'TOHOシネマズ日劇': {
        r'日劇': r'NICHIGEKI-'
    },
    'TOHOシネマズ高岡': {
        r'シネマ': r'SCREEN'
    },
    'TOHOシネマズなんば': {
        r'^\((\w+)\)(\w+)$': r'\1\2'
    },
    'TOHOシネマズ天神': {
        r'^(\w+)\((\w+)\)$': r'\2\1'
    }
}


def standardize_cinema_name(cinema_name):
    """
    standardize cinema name
    when handle special case like 'ＴＯＨＯシネマズなんば　本館・別館',
    trim words after space
    """
    if '本館' in cinema_name:
        cinema_name = cinema_name.split('本館')[0]
    cinema_name = standardize_name(cinema_name)
    return cinema_name


def standardize_screen_name(screen_name, cinema_name):
    """
    make sure screen name is same with those in order page,
    and convert all full width characters to half width
    """
    # remove full width first to avoid regex failure
    screen_name = standardize_name(screen_name)
    if is_screen_name_special(screen_name, cinema_name):
        screen_name = convert_special_screen_name(screen_name, cinema_name)
    return screen_name


def is_screen_name_special(screen_name, cinema_name):
    """
    check if given screen name is not same with screen name on cinemas table
    """
    # example:
    # (本館)SELECT -> 本館SELECT
    # SCREEN1(本館) -> 本館SCREEN1
    # シネマ1 -> SCREEN1
    # みゆき座 -> MIYUKIZA
    # 日劇1 -> NICHIGEKI-1
    # (TOHOシネマズシャンテ) SCREEN1 -> CHANTER-1
    return cinema_name in special_cinema


def convert_special_screen_name(screen_name, cinema_name):
    """
    some cinema have different screen name in order page and institution page,
    so we need to keep them same for further use.
    convert should only happen in toho_cinema spider
    """
    # replace special cinema screens
    if cinema_name in special_cinema:
        for key in special_cinema[cinema_name]:
            screen_name = re.sub(
                key, special_cinema[cinema_name][key], screen_name)
    return screen_name


def standardize_name(name):
    """
    remove all spaces, normalize full width characters to double width
    """
    name = unicodedata.normalize('NFKC', name)
    name = name.replace(' ', '')
    return name


class Cinema(scrapy.Item):
    name = scrapy.Field()
    county = scrapy.Field()
    company = scrapy.Field()
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
