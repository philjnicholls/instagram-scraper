"""Handles requests to get HTML."""
from urllib.parse import urlparse

from proxy_requests.constants import (
    READ_TIMEOUT_DEFAULT,
    CONNECTION_TIMEOUT_DEFAULT,
    RETRY_COUNT,
)
from proxy_requests.exceptions import FailedToGetHTML, NoMoreProxies

from proxyscrape import CollectorNotFoundError
from proxyscrape import create_collector, get_collector

import requests
from requests.adapters import HTTPAdapter
from  requests.adapters import Retry


class ProxyRequests():
    """Makes requests using scraped free proxies."""

    def __init__(self, filter_opts=None):
        self.http = None
        self.filter_opts = filter_opts

    def get(self, url, use_free_proxies=False):
        """Get Response from a URL.

        :param url: URL to get
        :param use_free_proxies: Use free proxies scraped from the web
        :return: HTML string
        """
        response = self._get(url, use_free_proxies=use_free_proxies)
        return response

    def get_html(self, url, use_free_proxies=False):
        """Get HTML from a URL.

        :param url: URL to get
        :param use_free_proxies: Use free proxies scraped from the web
        :return: HTML string
        """
        return self.get(url, use_free_proxies=use_free_proxies).text

    def _get(self, url, use_free_proxies=False):
        """Get Response from URL.

        :param url: URL to get
        :param use_free_proxies: Use free proxies scraped from the web
        :return: A Response object
        :raises FailedToGetHTML: If not HTML can be downloaded
        """
        http = self._get_session(use_free_proxies)
        while http:
            try:
                response = http.get(url,
                                    timeout=(CONNECTION_TIMEOUT_DEFAULT,
                                             READ_TIMEOUT_DEFAULT),
                                    stream=True)
                break
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ProxyError,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.RetryError):
                if use_free_proxies:
                    scheme = urlparse(url).scheme
                    proxy = http.proxies[scheme]
                    ProxyRequests._mark_proxy_as_bad(proxy)
                    http = self._get_session(use_free_proxies)
                    http.proxies = self._get_free_proxies()
                else:
                    raise FailedToGetHTML()

        if not response or response.status_code != 200:
            raise FailedToGetHTML()

        return response

    @staticmethod
    def _mark_proxy_as_bad(proxy):
        """Stop the relevant proxy being reused.

        :param proxy: Proxy to black list e.g. 'example.com:8080'
        """
        host = proxy.split(':')[0]
        port = proxy.split(':')[1]

        collector = ProxyRequests._get_free_proxies_collector()
        collector.blacklist_proxy(host, port)

    def _get_session(self, use_free_proxies=False):
        """Get a configured adapter and stores instance in class.

        :param use_free_proxies: Use free proxies scraped from the web
        :return: HTTPSession configured for use
        """
        if self.http:
            # Use existing session if one exists
            return self.http

        retry_strategy = Retry(
            total=RETRY_COUNT,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)
        if use_free_proxies:
            http.proxies = self._get_free_proxies()

        self.http = http
        return http

    @staticmethod
    def _get_free_proxies_collector():
        """Retrieve or create a Collector of free proxies.

        :return: Collector object
        """
        try:
            collector = get_collector('scraping-proxies')
        except CollectorNotFoundError:
            collector = create_collector('scraping-proxies',
                                         ['socks4', 'socks5'])

        return collector

    def _get_free_proxies(self):
        """Scrape free proxies form the web.

        :return: Dictionary of proxies for requests Session
        """
        collector = self._get_free_proxies_collector()
        proxy = collector.get_proxy(filter_opts=self.filter_opts)

        if proxy:
            return {'http': f'socks4://{proxy.host}:{proxy.port}',
                    'https': f'socks4://{proxy.host}:{proxy.port}'}
        raise NoMoreProxies
