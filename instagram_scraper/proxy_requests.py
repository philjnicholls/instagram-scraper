"""Handles requests to get HTML."""
import requests

from proxyscrape import CollectorNotFoundError
from proxyscrape import create_collector, get_collector
from proxyscrape import Proxy
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse

from instagram_scraper.exceptions import FailedToGetHTML, NoMoreProxies

from instagram_scraper import constants


def get(url, use_free_proxies=False):
    """Get Response from a URL.

    :param url: URL to get
    :param use_free_proxies: Use free proxies scraped from the web
    :return: HTML string
    """
    response = _get(url, use_free_proxies=False)
    return response

def get_html(url, use_free_proxies=False):
    """Get HTML from a URL.

    :param url: URL to get
    :param use_free_proxies: Use free proxies scraped from the web
    :return: HTML string
    """
    return get(url, use_free_proxies).text


def _get(url, use_free_proxies=False):
    """Get Response from URL

    :param url: URL to get
    :param use_free_proxies: Use free proxies scraped from the web
    :return: A Response object
    """
    http = _get_session(use_free_proxies)
    while(http):
        try:
            response = http.get(url,
                                timeout=(constants.CONNECTION_TIMEOUT_DEFAULT,
                                         constants.READ_TIMEOUT_DEFAULT),
                               stream=True)
            break
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ProxyError,
                requests.exceptions.ReadTimeout) as e:
            if use_free_proxies:
                _mark_proxy_as_bad(url, http.proxies)
                http = _get_session(use_free_proxies)
            else:
                raise FailedToGetHTML()

    if not response or response.status_code != 200:
        raise FailedToGetHTML()

    return response


def _mark_proxy_as_bad(url, proxies):
    """Stop the relevant proxy being reused.

    :param url: URL that the proxy was used for
    :param proxies: Proxies that were provided
    """
    scheme = urlparse(url).scheme
    collector = _get_free_proxies_collector()
    host = proxies[scheme].split(':')[0]
    port = proxies[scheme].split(':')[1]

    collector.blacklist_proxy(host, port)


def _get_session(use_free_proxies=False):
    """Get a configured adapter.

    :param use_free_proxies: Use free proxies scraped from the web
    :return: HTTPSession configured for use
    """
    adapter = HTTPAdapter()
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    if use_free_proxies:
        http.proxies = _get_free_proxies()
    return http


def _get_free_proxies_collector():
    """Retrieve or create a Collector of free proxies.

    :return: Collector object
    """
    try:
        collector = get_collector('scraping-proxies')
    except CollectorNotFoundError:
        collector = create_collector('scraping-proxies', ['socks4'])

    return collector


def _get_free_proxies():
    """Scrape free proxies form the web.

    :return: Dictionary of proxies for requests Session
    """
    proxy = _get_free_proxies_collector().get_proxy({'type': 'socks4'})

    if proxy:
        return {'http': f'socks4://{proxy.host}:{proxy.port}',
                'https': f'socks4://{proxy.host}:{proxy.port}'}
    else:
        return None
