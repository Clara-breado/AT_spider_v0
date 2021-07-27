from asyncio import tasks
import json
from queue import Queue
import time
import random
import os
import re
from attr import attr
import requests
import emoji
from fake_useragent import UserAgent
import asyncio
import aiohttp
import logging
import traceback
# 避免出现RuntimeError错误
# import nest_asyncio
# nest_asyncio.apply()
from lxml import etree
import pymongo
import sqlite3

class AT_review_spi:
    def __init__(self,base_url):
        # 初始化，连接MongoDB
        self.base_url = base_url
        self.client = pymongo.MongoClient('mongodb://localhost:27017/')
        self.success_get_count = 0
        self.success_test_count = 0
        self.failed_get_cnt = 0
        self.page_cnt = 0
        self.attr_name = ''
        self.dir_path = 'C:\\Users\\t-dohuang\\source\\repos\\TripAdvisor_spi\\London_data\\review\\{attr_name}'
        self.save_path = 'C:\\Users\\t-dohuang\\source\\repos\\TripAdvisor_spi\\London_data\\review\\{attr_name}\\{attr_name}{index}.json'
        self.db_file = 'C:\\Users\\t-dohuang\\Documents\\GitHub\\AT_spider\\review_urls.db'
        self.db_construct_flag = False
        self.request_queue = Queue()

        html = self.get_html(self.base_url.format(page=''))
        self.page_cnt = int(int(html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[11]/div[2]/div/div/text()[6]')[0].replace(',',''))/10)
        self.attr_name = html.xpath('//*[@id="lithium-root"]/main/div[1]/div[2]/div[1]/header/div[3]/div[1]/div/h1//text()')[0]
        cop = re.compile("['/','?',':','*','<','>','|',\u0022]")    #todo:'\'
        self.attr_name = cop.sub("",self.attr_name)
        #mkdir
        self.dir_path = self.dir_path.format(attr_name=self.attr_name)
        isExists = os.path.exists(self.dir_path)
        if not isExists:
            os.makedirs(self.dir_path)
            print ('mkdir:'+self.dir_path)
        else:
            print('alrady exists'+self.dir_path)

    def get_html(self,url):
        while True:
            try:
                header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
                html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
                
                html = emoji.demojize(html)
                cop = re.compile("[^\u0020-\u007e]")
                html = cop.sub('',html)

                selector = etree.HTML(html)
                str = etree.tostring(selector)

                return selector

            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
                randomtime = random.randint(1,5)
                logger.warn('ERROR - Retrying again website %s, retrying in %d secs' % (url, randomtime))
                time.sleep(randomtime)
                continue

    def init_review_urls_db(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            #create table
            create_table = '''CREATE TABLE IF NOT EXISTS {attr_name} (page int, url text, complete int)'''.format(attr_name = self.attr_name)
            c.execute(create_table)
            
            for i in range(-1,self.page_cnt):
                #start from sec
                bias = (i+1)*10     #10,20...52900,52910
                url = self.base_url.format(page='-or'+str(bias))
                insert_review_url = '''INSERT INTO {attr_name} VALUES({page},'{page_url}',0)'''.format(attr_name = self.attr_name,page = i+1,page_url = url)
                c.execute(insert_review_url)
            print(c.lastrowid)
            conn.commit()
            conn.close()
            self.db_construct_flag = True

        except Exception as e:
            logger.error("Cannot initiate table in %s" %self.db_file)
            logger.error(e)
            logger.error(traceback.format_exc())
            
    def init_review_urls_list(self):
        #read from db
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            #select urls which haven't completed
            select_url = '''SELECT page,url FROM {attr_name} WHERE complete = 0'''.format(attr_name = self.attr_name)
            c.execute(select_url)
            rows = c.fetchall() #rows is a list
            for row in rows:
                self.request_queue.put(row)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Cannot initiate table in %s" %self.db_file)
            logger.error(e)
            logger.error(traceback.format_exc())

    # 使用代理时，获取页面
    async def get_page(self, session, url):
        ## 一个随机生成请求头的库        
        ua = UserAgent()
        # 从本地文件获取代理池
        # proxies_pool = self.get_proxies()
        while True:
            try:
                # 由于我一开始操作不慎ip被封禁了，因此在一开始抓取ip时我不得不使用了自己从
                # 其他网站抓来的一批代理（如问题描述中所述），一共有5999条代理，每次随机选取一条
                # p = 'http://' + random.choice(proxies_pool)
                header = {'User-Agent': ua.random}
                prox = 'http://109.200.166.167:8080'
                async with session.get(url, headers = header,timeout = 20) as response:
                    await asyncio.sleep(10)
                    if response.status == 200:
                        self.success_get_count += 1
                        # if(self.success_get_count > 20):
                        #     self.failed_get_cnt -= 1
                        print("\033[5;36;40m----------------------请求成功-------------------%d次\033[;;m"%self.success_get_count)
                        return await response.text()
                    else:
                        print("\033[5;31;m", response.status, "\033[;;m")
                        continue
            except Exception as e:
                print("请求失败orz", e)
                self.failed_get_cnt += 1
                logger.error("Cannot Finish get page" )
                logger.error(e)
                logger.error(traceback.format_exc())
                if self.failed_get_cnt > 10:
                    time.sleep(30)
                    self.failed_get_cnt -= 5
                randomtime = random.randint(1,20)
                # header = {'User-Agent': ua.random}
                logger.warn('ERROR - Retrying again website %s, retrying in %d secs' % (url, randomtime))
                time.sleep(randomtime)    
        
    # 任务 entrance
    async def get(self):
        while True:
            try:
                [request_page,request_url] = self.request_queue.get()
                async with aiohttp.ClientSession() as session:
                    #get url from queue
                    html = await self.get_page(session, request_url)
                    html = emoji.demojize(html)
                    cop = re.compile("[^\u0020-\u007e]")
                    html = cop.sub('',html)
                    print("finish get page")
                    await self.get_detail(html,request_page)
                    break
            except Exception as e:
                logger.error("Cannot Finish GET" )
                logger.error(e)
                logger.error(traceback.format_exc())

                randomtime = random.randint(1,5)
                logger.warn('ERROR - Retrying again website %s, retrying in %d secs' % (url, randomtime))
                time.sleep(randomtime)
                continue      
    # 测试代理  
    async def test_proxy(self, dic):
        ## 根据类型构造不同的代理及url
        if dic["types"] == "HTTP":
            test_url = "http://www.baidu.com/"
            prop = "http://" + dic["proxies"]
        else:
            test_url = "https://www.baidu.com/"
            prop = "https://" + dic["proxies"]
        ua = UserAgent()
        header = {'User-Agent': ua.random}
        # 异步协程请求
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(test_url, headers = header, proxy = prop, timeout = 15, verify_ssl=False) as resp:
                        if resp.status == 200:
                            self.success_test_count += 1
                            print(prop, "\033[5;36;40m===========>测试成功，写入数据库!=========%d次\033[;;m"%self.success_test_count)
                            await self.insert_to_mongo(dic) ## 调用写入mongodb数据库的函数
                            return
                except Exception as e:
                    print(prop, "==测试失败,放弃==", e)
                    break
    
    # 获取代理池
    def get_proxies(self):
        with open("proxies.txt", "r") as f:
            ls = json.loads(f.read())
        return ls
    
    # 使用lxml爬取 
    async def get_detail(self, html,page):
        try:
            html = etree.HTML(html)
            review_dict = {}
            print("etree finish")
            for i in range(10):
                review = {}
                review_path = '//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[{index}]'.format(index=i+1)

                re_title = html.xpath(review_path+'/span/span/a/div/span/text()')
                if(len(re_title)>0):
                    re_title = re_title[0]
                else:
                    re_title = 'NONE'

                re_time = html.xpath(review_path+'/span/span/div[4]/text()')
                if len(re_time)==0:
                    re_time = 'NONE'
                    re_type = 'NONE'
                    re_body = html.xpath(review_path+'/span/span/div[4]/div[1]/div/span/text()')
                else:
                    re_time = re_time[0].encode('utf-8').decode('utf-8')
                    if ('  ' in re_time) is True:
                        [re_time,re_type] = re_time.split('  ')
                    else:
                        re_type = 'NONE'
                    re_body = html.xpath(review_path+'/span/span/div[5]/div[1]/div/span/text()')
                reviews = ''
                for re in re_body:
                    re = re.encode('utf-8').decode('utf-8')
                    reviews += re

                review['title'] = re_title
                review['time'] = re_time
                review['type'] = re_type
                review['review'] = reviews
                # print(re_title)  
                review_dict[page*10+i] = review
        #save to file
            path = self.save_path.format(attr_name=self.attr_name,index=page)
            f = open(path,"a")
            json.dump(review_dict,f,indent=2)

        #modified db
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            #update complete
            update_complete = '''UPDATE {attr_name} SET complete = 1 WHERE page = {up_page}'''.format(attr_name = self.attr_name,up_page = page)
            c.execute(update_complete)
            conn.commit()
            conn.close()

        except Exception as e:
                logger.error("Cannot Finish GET Detail" )
                logger.error(e)
                logger.error(traceback.format_exc())
        # ip = html.xpath('//tr[@class="odd" or @class=""]/td[2]/text()')
        # port = html.xpath('//tr[@class="odd" or @class=""]/td[3]/text()')
        # types = html.xpath('//tr[@class="odd" or @class=""]/td[6]/text()')
        # for i in range(len(ip)):
        #     dic['proxies'] = ip[i] + ":" + port[i]
        #     dic['types'] = types[i]
        #     await self.test_proxy(dic)
    # async def insert_to_json(self,review,page):
    #     try:
    #         #write dic to json file

    #     except Exception as e:

    # 写入MongoDB数据库   
    async def insert_to_mongo(self, dic):
        db = self.client.Myproxies
        collection = db.proxies
        collection.update_one(dic,{'$set': dic}, upsert=True)   # 设置upsert=True，避免重复插入
        print("\033[5;32;40m插入记录：" + json.dumps(dic), "\033[;;m")
    
    def multi_thread(self):
        try:
            print(self.request_queue.qsize())
            tasks = [asyncio.ensure_future(self.get()) for _ in range(self.request_queue.qsize())]
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.wait(tasks))
        except Exception as e:
            logger.error('multi_thread failed!')
            logger.error(e)
# 主线程
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('AT_Spider.log')
    formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


    urls = []
    start = time.time()
    base_url = 'https://www.tripadvisor.in/Attraction_Review-g186338-d218015-Reviews{page}-Westminster-London_England.html'
    # 抓取前10页数据
    for i in range(1, 11):
        bias = (i+1)*10     #10,20...52900,52910
        url = base_url.format(page='-or'+str(bias))    
        urls.append(url)
    c = AT_review_spi(base_url)

    conn = sqlite3.connect(c.db_file)
    cur = conn.cursor()
    cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{attr_name}' '''.format(attr_name = c.attr_name))

    #if the count is 1, then table exists
    if cur.fetchone()[0]==1 : {
        print('Table exists.')
    }
    else:
        c.init_review_urls_db()
                
    #commit the changes to db			
    conn.commit()
    #close the connection
    conn.close()


    # c.db_construct_flag = True
    # if c.db_construct_flag is False:
    #     c.init_review_urls_db()
    
    c.init_review_urls_list()

    c.multi_thread()
        #start crawling

    #init table for single attraction

    #insert urls to the table

    # 创建10个未来任务对象
    # tasks = [asyncio.ensure_future(c.get(url)) for url in urls]
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(asyncio.wait(tasks))
    end = time.time()
    total = (end - start)/60.0
    print("完成，总耗时:", total, "分钟!")