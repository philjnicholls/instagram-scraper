"""Spider to scrape posts from Instagram users."""
import json
from urllib.parse import urlencode

from instagram_scraper.helpers import node_to_post

import scrapy


class InstagramSpider(scrapy.Spider):
    """Spider to extract Instagram posts for a list of users."""

    name = 'instagram_users'

    def __init__(self, users, **kwargs):
        """Split commas separated users into a list.

        :param users: Commas separated list of users
        :param kwargs: Any additional parameters to pass to parent
        """
        self.users = users.split(',')
        super().__init__(**kwargs)

    def start_requests(self):
        """Loop over users and yield results.

        :yields: Response of each usernames Instagram posts
        """
        for username in self.users:
            url = f'https://www.instagram.com/{username}/?hl=en'
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """Parse just the first page.

        :param response: HTML from first page of Instagram posts
        :yields: An dictionary of Instagram post data
        """
        script = response.xpath('//script[starts-with('
                                '.,\'window._sharedData\')]'
                                "/text()").extract_first()
        json_string = script.strip().split('= ')[1][:-1]
        data = json.loads(json_string)

        user_id = data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        next_page_bool = data[
            'entry_data']['ProfilePage'][0]['graphql'][
                'user']['edge_owner_to_timeline_media']['page_info'][
                    'has_next_page']
        edges = data[
            'entry_data']['ProfilePage'][0]['graphql'][
                'user']['edge_felix_video_timeline']['edges']

        for i in edges:
            item = node_to_post(i['node'])
            yield item

        if next_page_bool:
            cursor = data[
                'entry_data']['ProfilePage'][0]['graphql'][
                    'user']['edge_owner_to_timeline_media'][
                        'page_info']['end_cursor']
            di = {'id': user_id, 'first': 12, 'after': cursor}
            params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08',
                      'variables': json.dumps(di)}
            url = (f'https://www.instagram.com/graphql/query/?'
                   f'{urlencode(params)}')
            yield scrapy.Request(url,
                                 callback=self.parse_pages,
                                 meta={'pages_di': di})

    def parse_pages(self, response):
        """Parse remaining pages after the first page.

        :param response: Response object containing the post JSON
        :yields: A dictionary of Instagram post data
        """
        di = response.meta['pages_di']
        data = json.loads(response.text)

        for i in data['data']['user']['edge_owner_to_timeline_media']['edges']:
            item = node_to_post(i['node'])
            yield item

        next_page_bool = data[
            'data']['user']['edge_owner_to_timeline_media'][
                'page_info']['has_next_page']
        if next_page_bool:
            cursor = data[
                'data']['user']['edge_owner_to_timeline_media'][
                    'page_info']['end_cursor']
            di['after'] = cursor
            params = {'query_hash': 'e769aa130647d2354c40ea6a439bfc08',
                      'variables': json.dumps(di)}
            url = (f'https://www.instagram.com/graphql/query/?'
                   f'{urlencode(params)}')
            yield scrapy.Request(url,
                                 callback=self.parse_pages,
                                 meta={'pages_di': di})
