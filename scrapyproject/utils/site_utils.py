"""
module that include utility function to help crawl site
"""
import os
import re
import requests


def standardize_county_name(county_name):
    """
    standardize county name to full name
    """
    if county_name in ["東京都23区内", "東京都下"]:
        return "東京都"
    elif county_name == "東京":
        return county_name + "都"
    elif county_name in ["大阪", "京都"]:
        return county_name + "府"
    elif county_name in ["北海道", "東京都", "大阪府", "京都府"]:
        return county_name
    elif "県" not in county_name:
        # "北海道" not included
        return county_name + "県"
    else:
        return county_name


def standardize_site_url(url, cinema):
    """
    change crawled cinema site url as some data are wrong
    """
    if "ジストシネマ和歌山" in cinema['names']:
        return "http://www.o-entertainment.co.jp"\
               "/xyst_cinema/wakayama/information.html"
    elif "ジストシネマ御坊" in cinema['names']:
        return "http://www.o-entertainment.co.jp"\
               "/xyst_cinema/gobo/information.html"
    elif "ジストシネマ田辺" in cinema['names']:
        return "http://www.o-entertainment.co.jp"\
               "/xyst_cinema/tanabe/information.html"
    elif "ジストシネマ南紀" in cinema['names']:
        return "http://www.o-entertainment.co.jp"\
               "/xyst_cinema/nanki/information.html"
    elif "ジストシネマ伊賀上野" in cinema['names']:
        return "http://www.o-entertainment.co.jp"\
               "/xyst_cinema/igaueno/information.html"
    else:
        return url


def standardize_book_status(book_status):
    """
    standardize book status

    toho site:
    A Plenty Left
    B Half full
    C Few Seats Left
    D Sold Out
    G Not Sold
    """
    if book_status == 'A':
        return "PlentyLeft"
    elif book_status == 'B':
        return "HalfFull"
    elif book_status == 'C':
        return "FewSeatsLeft"
    elif book_status == 'D':
        return "SoldOut"
    else:
        # 'G' for toho site
        return "NotSold"


def extract_seat_number(seat_str):
    """
    extract seat count from given screen

    when mulitple number is extracted use larger one
    edge case:
    "(2D・IMAX)383 / (3D・IMAX)345"
    """
    seats_count_list = [int(_) for _ in re.findall(r"\d+", seat_str)]
    if seats_count_list:
        return max(seats_count_list)
    else:
        return 0


def do_proxy_request(url, **kwargs):
    """
    start a request using proxy
    """
    proxy_str = (os.environ['PROXY_TYPE'] + '://user:pass@'
                 + os.environ['PROXY_ADDRESS'] + ':' + os.environ['PROXY_PORT'])
    proxies = {
        'http': proxy_str,
        'https': proxy_str
    }
    r = requests.get(url, **dict(kwargs, proxies=proxies))
    return r
