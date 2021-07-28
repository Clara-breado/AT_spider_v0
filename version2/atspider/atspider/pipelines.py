# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from itemadapter import ItemAdapter

class AtspiderPipeline:
    # def process_item(self, item, spider):
    #     return item
    def open_spider(self, spider):
        spider.data = {}
        print("\033[5;36;40m----------------------open-------------------次\033[;;m")
        # self.file = open('C:\\Users\\t-dohuang\\Documents\\GitHub\\atspider\\reviews_test.json', 'a')
        # self.file.write('open file!!!\n')
    def close_spider(self, spider):
        # self.file.write(json.dumps(spider.data))
        print("\033[5;36;40m----------------------close-------------------次\033[;;m")
        # self.file.close()

    def process_item(self, item, spider):
        # try:
        #     spider.data[item['place']]['review'].append(item['attr_reviews'])
        #     print("\033[5;36;40m----------------------process-------------------次\033[;;m")
        # except: pass
        # return item
        page = ItemAdapter(item).asdict()['attr_page']
        print("\033[5;36;40m----------------------%d page-------------------次\033[;;m"%page)
        self.file = open('C:\\Users\\t-dohuang\\Documents\\GitHub\\atspider\\reviews_{page}.json'.format(page=page), 'a')
        # line = json.dumps(ItemAdapter(item).asdict()) + "\n"
        line = json.dumps(ItemAdapter(item).asdict(),indent=2)
        self.file.write(line)
        self.file.close()
        print("\033[5;36;40m----------------------write-------------------次\033[;;m")
        return item

class JsonWriterPipeline:

    def open_spider(self, spider):
        self.file = open('items.jl', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(ItemAdapter(item).asdict()) + "\n"
        self.file.write(line)
        return item