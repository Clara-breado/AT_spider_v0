# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

#item for attractions' other info
class AtspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # attr_name = scrapy.Field()
    attr_name = scrapy.Field()
    # attr_page = scrapy.Field()
    # attr_reviews = scrapy.Field()

    attr_info = scrapy.Field()
    pass

#item for attractions' reviews
class ReviewsItem(scrapy.Item):
    attr_name = scrapy.Field()
    # attr_page_cnt = scrapy.Field()
    attr_page = scrapy.Field()
    attr_reviews = scrapy.Field()
    pass