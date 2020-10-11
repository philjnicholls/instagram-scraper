"""Exceptions package."""


class FailedToGetHTML(Exception):
    """Failed to get HTML for page."""


class NoMoreProxies(Exception):
    """No more free proxies could be found."""
