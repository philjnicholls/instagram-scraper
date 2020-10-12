"""Spider to scrape posts from Instagram tags."""
import json
import re

from instagram_scraper.helpers import node_to_post

import scrapy


class InstagramSpider(scrapy.Spider):
    """Spider to extract Instagram posts for a list of tags."""

    name = 'instagram_tags'

    def __init__(self, tags, **kwargs):
        """Split commas separated users into a list.

        :param tags: Commas separated list of tags
        :param kwargs: Any additional parameters to pass to parent
        """
        self.tags = tags.split(',')
        super().__init__(**kwargs)

    def start_requests(self):
        """Loop over tags and yield results.

        :yields: Response of each usernames Instagram posts
        """
        for tag in self.tags:
            url = f'https://www.instagram.com/explore/tags/{tag}/'
            yield scrapy.Request(url, callback=self.parse)

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
        tag = data['entry_data']['TagPage'][0]['graphql']['hashtag']['name']
        # all that we have to do here is to parse the JSON we have
        next_page_bool = data[
            'entry_data']['TagPage'][0]['graphql']['hashtag'][
                'edge_hashtag_to_media']['page_info']['has_next_page']
        edges = data[
            'entry_data']['TagPage'][0]['graphql']['hashtag'][
                'edge_hashtag_to_media']['edges']
        for i in edges:
            item = node_to_post(i['node'])
            yield item
        if next_page_bool:
            cursor = data[
                'entry_data']['TagPage'][0]['graphql']['hashtag'][
                    'edge_hashtag_to_media']['page_info']['end_cursor']
            url = (f'https://www.instagram.com/graphql/query/'
                   f'?query_hash=298b92c8d7cad703f7565aa892ede943&'
                   f'variables={{"tag_name":"{tag}","first":12,'
                   f'"after":"{cursor}"}}')
            yield scrapy.Request(url, callback=self.parse_pages)

    def parse_pages(self, response):
        """Parse remaining pages after the first page.

        :param response: Response object containing the post JSON
        :yields: A dictionary of Instagram post data
        """
        data = json.loads(response.text)
        tag = data['data']['hashtag']['name']
        for i in data['data']['hashtag']['edge_hashtag_to_media']['edges']:
            item = node_to_post(i['node'])
            yield item
        next_page_bool = data['data']['hashtag']['edge_hashtag_to_media'][
            'page_info']['has_next_page']
        if next_page_bool:
            cursor = data[
                'data']['hashtag']['edge_hashtag_to_media'][
                    'page_info']['end_cursor']
            url = (f'https://www.instagram.com/graphql/query/'
                   f'?query_hash=298b92c8d7cad703f7565aa892ede943&'
                   f'variables={{"tag_name":"{tag}","first":12,'
                   f'"after":"{cursor}"}}')
            yield scrapy.Request(url, callback=self.parse_pages)
