# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import unicodedata


def standardize_cinema_name(cinema_name):
    """
    standardize cinema name with related info like screen count and conuty
    """
    # first, make sure only half width charaters left
    cinema_name = unicodedata.normalize('NFKC', cinema_name)
    # second, remove all spaces
    cinema_name = cinema_name.replace(' ', '')
    return cinema_name


def standardize_screen_name(screen_name, cinema):
    """
    standardize screen name, make sure screen can be queried in database
    """
    # first, make sure only half width charaters left
    screen_name = unicodedata.normalize('NFKC', screen_name)
    # second, remove all spaces
    screen_name = screen_name.replace(' ', '')
    return screen_name
