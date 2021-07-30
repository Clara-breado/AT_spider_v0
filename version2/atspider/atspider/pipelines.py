# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from os import name
from atspider.items import AtspiderItem, ReviewsItem
from itemadapter import ItemAdapter
import json
import logging
import time
import os
from collections import OrderedDict
from twisted.enterprise import adbapi
class AtspiderPipeline:
    attrs = {}
    PROC_CNT = 0
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('AT_Spider_1.log')
    formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # def process_item(self, item, spider):
    #     return item
    def open_spider(self, spider):
        spider.data = {}
        print("\033[5;36;40m----------------------open-------------------次\033[;;m")
    def close_spider(self, spider):
        self.file = open('Europe_Italy__info.json'.format(attr_name=name), 'a')
        line = json.dumps(self.attrs,indent=2)
        self.file.write(line)
        self.file.close()
        self.logger.info("end time: %s" %str(time.time()))
        self.logger.info("item cnt: %d" %self.PROC_CNT)
        print("\033[5;36;40m----------------------close-------------------次\033[;;m")
        # self.logger.info("PROC cnt is %d" %self.PROC_CNT)

    def process_item(self, item, spider):
        self.PROC_CNT += 1
        if type(item)==AtspiderItem:
            name = ItemAdapter(item).asdict()['attr_name']
            self.attrs['{attr_name}'.format(attr_name = name)] = ItemAdapter(item).asdict()


            return item        
        else:
            pass

class ReviewsItemPipeline:
    index = 0
    reviews_cnt = 0
    reviews = {}
    dir_path = 'C:\\Users\\t-dohuang\\Documents\\GitHub\\atspider\\dataset\\{attr_name}'
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('AT_Spider.log')
    formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def open_spider(self, spider):
        # self.file = open('items.jl', 'w')
        self.logger.info("ReviewsItemPipelin run")
    def close_spider(self, spider):
        # self.file.close()
        with open('reviews.json', 'a') as file:
            file.write(json.dumps(self.reviews,indent = 2))
        self.logger.info("ReviewsItemPipelin stop")
    def process_item(self, item, spider):
        try:
            if type(item)==ReviewsItem:
                self.reviews[self.reviews_cnt] = ItemAdapter(item).asdict()
                self.reviews_cnt += 1
                self.logger.info(self.reviews_cnt)
        except Exception as e:
            self.logger.error(e)
        return item  

# # class DbPipeLine(object):
#     #数据库存储管道，具有异步存储和多类item处理能力
#     def __init__(self, db_config):
#         # 建立数据库连接池
#         self.dbpool = adbapi.ConnectionPool(
#             db_config['driver'],
#             host=db_config['host'],
#             port=db_config['port'],
#             user=db_config['user'],
#             db=db_config['db'],
#             charset=db_config['charset']  # 此处为utf8，不是utf-8，也没有逗号
#         )

#     @classmethod
#     def from_crawler(cls, crawler):
#         #重写，以获取settings模块相关信息，每次创建该pipeline时，就会调用此方法
#         #    cls：代表自身类DbPipeLine
#         #    crawler：为爬虫项目类，包含spider,settings等属性
#         db_config = crawler.settings['DB_CONFIG']     #DB_CONFIG为数据库登录信息
#         return cls(db_config)  # 相当 于DbPipeLine(db_config )

#     def process_item(self, item, spider):
#         #固定函数名，用于处理spider传递的item类型数据
#         #runInteraction：可获取连接池中数据库的游标cursor，并将游标和数值传递给回调函数
#         #result：接收返回的操作结果
#         #通过if语句实现多类型item的不同操作
#         if isinstance(item,ReviewsItem):
#             result = self.dbpool.runInteraction(self.insert_fl, item)
#             result.addErrback(self.print_erro)
#         return item

#     def insert_fl(self, cursor, item):
#         #定义sql插入语句，并留坑
#         sql = "INSERT INTO fl(" \
#               "fl_id," \
#               "fl_title," \
#               "fl_content," \
#               "fl_region" \
#               "VALUE(%s,%s,%s,%s)"
#         args = (
#             item['fl_id'],
#             item['fl_title'],
#             item['fl_content'],
#             item['fl_region'],
#         )
#         cursor.execute(sql, args)


#     def print_erro(self, failure):
#         # 打印错误信息
#         print(failure)


#     def close_spider(self, spiders):
#         # 关闭链接池
#         self.dbpool.close()
