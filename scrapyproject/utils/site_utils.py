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
    elif county_name == "北海道":
        return county_name
    elif county_name in ["大阪", "京都"]:
        return county_name + "府"
    elif "県" not in county_name:
        # "北海道" not included
        return county_name + "県"
    else:
        return county_name


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
