# Instagram Scraper

Uses scrapy to scrape Instagram posts from a list of users, hashtags or
locations and dump to a CSV.
Includes a custom written proxy rotator which makes use of proxyscrape to
rotate through free proxies scraped from the web.

# Usage

scrapy crawl instagram_users -a users=nike -o nike.csv

scrapy crawl instagram_tags -a tags=blacklivesmatter,100daysofcode -o blacklivesmatter_100daysofcode.csv

scrapy crawl instagram_locations -a locations=110589025635590,644767678 -o prague_fremantle.csv
