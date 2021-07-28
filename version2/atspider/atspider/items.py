# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AtspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # attr_name = scrapy.Field()
    attr_name = scrapy.Field()
    attr_page = scrapy.Field()
    attr_reviews = scrapy.Field()
    pass
