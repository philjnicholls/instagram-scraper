"""Helper functions for use in spiders."""
from datetime import datetime

import scrapy


def node_to_post(node):
    """Covert Instragram post data format to item format.

    :param node: Instagram data in dict
    :returns: Dict in updated, flatter format
    """
    url = 'https://www.instagram.com/p/' + node['shortcode']
    video = node['is_video']
    date_posted_timestamp = node['taken_at_timestamp']
    date_posted_human = datetime.fromtimestamp(
        date_posted_timestamp).strftime("%d/%m/%Y %H:%M:%S")
    like_count = node['edge_liked_by'][
        'count'] if "edge_liked_by" in node.keys() else ''
    comment_count = node['edge_media_to_comment'][
        'count'] if 'edge_media_to_comment' in node.keys() else ''
    owner = node['owner'][
        'username'] if 'username' in node['owner'] else node['owner']['id']
    captions = ""
    if node['edge_media_to_caption']:
        captions = '\n'.join(caption['node'][
            'text'] for caption in node['edge_media_to_caption']['edges'])

    if video:
        if 'video_url' in node:
            video_url = node['video_url']
        else:
            video_url = ''
        image_url = node['display_url']
        video_view_count = node['video_view_count']
    else:
        video_url = ''
        video_view_count = ''
        image_url = node['thumbnail_resources'][-1]['src']

    item = {'post_url': url,
            'owner': owner,
            'is_video': video,
            'date_posted': date_posted_human,
            'timestamp': date_posted_timestamp,
            'like_count': like_count,
            'comment_count': comment_count,
            'image_url': image_url,
            'video_url': video_url,
            'video_view_count': video_view_count,
            'captions': captions[:-1]}

    if item['is_video'] and not item['video_url']:
        return scrapy.Request(item['post_url'],
                              callback=get_video,
                              meta={'item':
                                    item})

    return item


def get_video(response):
    """Get the video url from the post page.

    :param response: Response of the post page
    :returns: Updated post dictionary
    """
    item = response.meta['item']
    video_url = response.xpath(
        '//meta[@property="og:video"]/@content').extract_first()
    item['video_url'] = video_url
    return item
