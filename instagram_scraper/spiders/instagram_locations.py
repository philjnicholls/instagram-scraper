"""Spider to scrape posts from Instagram locations."""
import json
import re

from instagram_scraper.helpers import node_to_post

import scrapy


class InstagramSpider(scrapy.Spider):
    """Spider to extract Instagram posts for a list of locations."""

    name = 'instagram_locations'

    def __init__(self, locations, country=None, **kwargs):
        """Split commas separated locations into a list.

        :param locations: Commas separated list of locations
        :param kwargs: Any additional parameters to pass to parent
        """
        self.locations = locations.split(',')
        self.country = country
        super().__init__(**kwargs)

    def start_requests(self):
        """Loop over locations and yield results.

        :yields: Response of each usernames Instagram posts
        """
        for location in self.locations:
            url = f'https://www.instagram.com/explore/locations/{location}/'
            yield scrapy.Request(url,
                                 callback=self.parse,
                                 meta={'country': self.country})

    def parse(self, response):
        """Parse just the first page.

        :param response: HTML from first page of Instagram posts
        :yields: An dictionary of Instagram post data
        """
        script = response.xpath('//script['
                                'starts-with(.,\'window._sharedData\')]'
                                '/text()').extract_first()
        json_string = re.match(r'.*?(\{.*\}).*?', script).group(1)
        data = json.loads(json_string)
        location_id = data[
            'entry_data']['LocationsPage'][0]['graphql']['location']['id']
        # all that we have to do here is to parse the JSON we have
        next_page_bool = data[
            'entry_data']['LocationsPage'][0]['graphql']['location'][
                'edge_location_to_media']['page_info']['has_next_page']
        edges = data[
            'entry_data']['LocationsPage'][0]['graphql']['location'][
                'edge_location_to_media']['edges']
        for i in edges:
            item = node_to_post(i['node'])
            yield item
        if next_page_bool:
            cursor = data[
                'entry_data']['LocationsPage'][0]['graphql']['location'][
                    'edge_location_to_media']['page_info']['end_cursor']
            url = (f'https://www.instagram.com/graphql/query/'
                   f'?query_hash=ac38b90f0f3981c42092016a37c59bf7&'
                   f'variables={{"id":"{location_id}","first":12,'
                   f'"after":"{cursor}"}}')
            yield scrapy.Request(url, callback=self.parse_pages)

    def parse_pages(self, response):
        """Parse remaining pages after the first page.

        :param response: Response object containing the post JSON
        :yields: A dictionary of Instagram post data
        """
        data = json.loads(response.text)
        location_id = data['data']['location']['id']
        for i in data['data']['location']['edge_location_to_media']['edges']:
            item = node_to_post(i['node'])
            yield item
        next_page_bool = data['data']['location']['edge_location_to_media'][
            'page_info']['has_next_page']
        if next_page_bool:
            cursor = data[
                'data']['location']['edge_location_to_media'][
                    'page_info']['end_cursor']
            url = (f'https://www.instagram.com/graphql/query/'
                   f'?query_hash=ac38b90f0f3981c42092016a37c59bf7&'
                   f'variables={{"id":"{location_id}","first":12,'
                   f'"after":"{cursor}"}}')
            yield scrapy.Request(url, callback=self.parse_pages)

