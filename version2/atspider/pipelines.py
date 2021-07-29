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
class AtspiderPipeline:
    PROC_CNT = 0
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('AT_Spider.log')
    formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # def process_item(self, item, spider):
    #     return item
    def open_spider(self, spider):
        spider.data = {}
        print("\033[5;36;40m----------------------open-------------------次\033[;;m")
    def close_spider(self, spider):
        self.logger.info("end time: %s" %str(time.time()))
        print("\033[5;36;40m----------------------close-------------------次\033[;;m")
        # self.logger.info("PROC cnt is %d" %self.PROC_CNT)

    def process_item(self, item, spider):
        # page = ItemAdapter(item).asdict()['attr_page']
        # print("\033[5;36;40m----------------------%d page-------------------次\033[;;m"%page)
        # self.file = open('C:\\Users\\t-dohuang\\Documents\\GitHub\\atspider\\dataset\\Little_Venice__reviews_{page}.json'.format(page=page), 'a')
        # self.PROC_CNT += 1
        # line = json.dumps(ItemAdapter(item).asdict(),indent=2)
        # self.file.write(line)
        # self.file.close()
        # return item
        if type(item)==AtspiderItem:
            name = ItemAdapter(item).asdict()['attr_name']
            self.file = open('C:\\Users\\t-dohuang\\Documents\\GitHub\\atspider\\dataset\\{attr_name}__info.json'.format(attr_name=name), 'w')
            line = json.dumps(ItemAdapter(item).asdict(),indent=2)
            self.file.write(line)
            self.file.close()
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
        self.logger.info("ReviewsItemPipelin stop")
    def process_item(self, item, spider):
        if type(item)==ReviewsItem:
            name = ItemAdapter(item).asdict()['attr_name']
            # page_cnt = ItemAdapter(item).asdict()['attr_page_cnt']

            #mkdir
            dir_path = self.dir_path.format(attr_name=name)
            isExists = os.path.exists(dir_path)
            if not isExists:
                print("\033[5;36;40m----------------------make dir!!!!!-------------------次\033[;;m")
                os.makedirs(dir_path)
                self.logger.info('mkdir:%s' %dir_path)
            #put file in dir
            page = ItemAdapter(item).asdict()['attr_page']
            # print("\033[5;36;40m----------------------%d page-------------------次\033[;;m"%page)
            # if self.reviews_cnt>3:
            #     self.index += 1
            #     self.reviews_cnt = 0

            # if (self.reviews_cnt <20)and(self.reviews_cnt<page_cnt):
            #     self.reviews[self.reviews_cnt] = ItemAdapter(item).asdict()
            #     self.reviews_cnt += 1
            # else:
                # self.reviews_cnt = 0
                # self.index += 1
            file_path = dir_path+'\\{attr_name}__reviews_{index}.json'.format(attr_name=name,index=page)
            self.file = open(file_path, 'a')
            line = json.dumps(ItemAdapter(item).asdict(),indent=2)
            self.file.write(line)
            self.reviews = {}
            print("\033[5;36;40m----------------------save!!!!!-------------------次\033[;;m")
            self.file.close()
            return item  
