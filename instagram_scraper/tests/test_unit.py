"""Unit tests for Instagram Scraper."""
import re

from instagram_scraper import requests
from instagram_scraper.instagram_scraper import Scraper

from instagram_scraper.proxy_requests import get as no_proxy_get


def test_get_page():
    """Try to get a simple webpage."""
    breakpoint()
    response = no_proxy_get('https://www.whatsmyip.org/')
    ip = re.search('<h1>.*?(\d+\.\d+\.\d+\.\d+).*</h1>',
                   response.text).group(1)
    assert ip not in requests.get('https://www.whatsmyip.org/',
                                  use_free_proxies=True)
