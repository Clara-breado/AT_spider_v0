# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from atspider.items import AtspiderItem
from itemadapter import ItemAdapter
import json
import logging
import time
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
    def open_spider(self, spider):
        self.file = open('items.jl', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict()) + "\n"
        self.file.write(line)
        return item