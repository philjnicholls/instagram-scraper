"""Unit tests for Instagram Scraper."""
import requests

from proxy_requests import proxy_requests


def test_different_ip_with_proxy():
    """Try to get a simple webpage."""
    response = requests.get('https://api.ipify.org/')
    ip_address = response.text
    assert ip_address not in proxy_requests.get_html(
        'https://api.ipify.org/',
        use_free_proxies=True)


def test_same_ip_with_no_proxy():
    """Try to get a simple webpage."""
    response = requests.get('https://api.ipify.org/')
    ip_address = response.text
    assert ip_address in proxy_requests.get_html(
        'https://api.ipify.org/',
        use_free_proxies=False)
