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


def do_proxy_request(url=None, method="GET", data=None, **kwargs):
    """
    start a request using proxy
    """
    proxy_str = (os.environ['PROXY_TYPE'] + '://user:pass@'
                 + os.environ['PROXY_ADDRESS'] + ':'
                 + os.environ['PROXY_PORT'])
    proxies = {
        'http': proxy_str,
        'https': proxy_str
    }
    r = requests.request(
        method=method, url=url, data=data, proxies=proxies, **kwargs)
    # fix encoding problem in requests
    # python does not support "Windows-31J"
    if r.encoding and r.encoding.lower() in [
            x.lower() for x in ["no value", "ISO-8859-1", "Windows-31J"]]:
        r.encoding = r.apparent_encoding
    return r


class TohoUtil(object):
    @staticmethod
    def generate_cinema_homepage_url(site_cd):
        return 'https://hlo.tohotheater.jp/net/schedule/{site_cd}'\
               '/TNPI2000J01.do'.format(site_cd=site_cd)

    @staticmethod
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
            return "PlentyLeft"
        elif book_status == 'B':
            return "HalfFull"
        elif book_status == 'C':
            return "FewSeatsLeft"
        elif book_status == 'D':
            return "SoldOut"
        else:
            # 'G'
            return "NotSold"


class CinemaSunshineUtil(object):
    @staticmethod
    def standardize_book_status(book_status):
        # seems status "3" is not used now...
        if book_status == "0":
            return "PlentyLeft"
        elif book_status == "2":
            return "HalfFull"
        elif book_status == "5":
            return "SoldOut"
        else:
            # "1" "4" 6"
            return "NotSold"


class ForumUtil(object):
    @staticmethod
    def standardize_book_status(book_status):
        # use css to judge book status
        # seems css "soldout" is used for not sold...
        # TODO we still don't know how sold out is presented
        if book_status == "purchase vacancy":
            return "PlentyLeft"
        if book_status == "purchase little":
            return "FewSeatsLeft"
        elif book_status == "purchase soldout":
            return "NotSold"
        else:
            return "NotSold"


class KoronaUtil(object):
    @staticmethod
    def standardize_book_status(book_status):
        # use image alt attribute to determine book status
        # TODO we don't know how sold out is presented, maybe should use time
        if book_status == "空席90％以上":
            return "PlentyLeft"
        elif book_status == "空席90％未満":
            return "HalfFull"
        elif book_status == "空席50％未満":
            return "FewSeatsLeft"
        elif book_status == "空席10％未満":
            return "NotSold"


class AeonUtil(object):
    @staticmethod
    def standardize_seat_type(seat_type):
        if "自由席" in seat_type:
            return "FreeSeat"
        else:
            return "NormalSeat"

    @staticmethod
    def standardize_book_status(book_status):
        if book_status == "◎":
            return "PlentyLeft"
        elif book_status == "○":
            return "HalfFull"
        elif book_status == "△":
            return "FewSeatsLeft"
        elif book_status == "×":
            return "SoldOut"
        elif book_status == "e席受付終了":
            return "NotSold"
        else:
            return "NotSold"


class UnitedUtil(object):
    @staticmethod
    def standardize_seat_type(seat_type):
        if "icon_09.gif" in seat_type:
            return "FreeSeat"
        else:
            return "NormalSeat"

    @staticmethod
    def standardize_book_status(book_status):
        if "icon_15_s" in book_status:
            return "PlentyLeft"
        elif "icon_16_s" in book_status:
            return "FewSeatsLeft"
        elif "icon_17_s" in book_status:
            return "SoldOut"
        elif "icon_18_s" in book_status:
            return "NotSold"
        else:
            return "NotSold"


class MovixUtil(object):
    @staticmethod
    def standardize_book_status(book_status):
        # TODO sold out status can only be judged with date and time
        if "01.png" in book_status:
            return "PlentyLeft"
        elif "02.png" in book_status:
            return "FewSeatsLeft"
        elif "03.png" in book_status:
            return "NotSold"
        elif "04.png" in book_status:
            return "NotSold"
        else:
            return "NotSold"


class KinezoUtil(object):
    @staticmethod
    def standardize_book_status(book_status):
        if "scType01" in book_status:
            return "PlentyLeft"
        elif "scType02" in book_status:
            return "HalfFull"
        elif "scType03" in book_status:
            return "FewSeatsLeft"
        elif "scType04" in book_status:
            return "NotSold"
        elif "scType05" in book_status:
            return "SoldOut"
        elif "scType06" in book_status:
            return "NotSold"
        elif "scType07" in book_status:
            return "NotSold"
        else:
            return "NotSold"


class Site109Util(object):
    @staticmethod
    def standardize_book_status(book_status):
        if "available" in book_status:
            return "PlentyLeft"
        elif "remaining" in book_status:
            return "HalfFull"
        elif "soldout" in book_status:
            return "SoldOut"
        elif "close" in book_status:
            return "NotSold"
        else:
            return "NotSold"
