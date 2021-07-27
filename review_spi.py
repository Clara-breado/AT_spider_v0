import os
import sys
import logging
import random
import emoji
import requests
import json
import re
from lxml import etree
import time
import threading
import traceback
from queue import Queue
from threading import Thread
import asyncio
from requests.models import Response

from requests.sessions import session
import aiohttp

##one object for one attraction
class AT_view_spider:
    def __init__(self,base_url):
        self.base_url = base_url
        #start_url include format!!!
        self.review_request_queue = Queue()
        self.review_get_queue = Queue()
        self.index_queue = Queue()
        self.page_cnt = 0
        self.review_cnt = 0
        self.max_review = 10    #20 review in one json file
        self.url_list = []
        self.review_dict = []
        self.attr_name = ''
        self.dir_path = 'C:\\Users\\t-dohuang\\source\\repos\\TripAdvisor_spi\\London_data\\review\\{attr_name}'
        self.save_path = 'C:\\Users\\t-dohuang\\source\\repos\\TripAdvisor_spi\\London_data\\review\\{attr_name}\\{attr_name}{index}.json'
        self.flag = False
        self.GET_finish = False
        self.USE_finish = False
        self.SAVE_finish = False

    def get_html(self,url):
        # header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
        # html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        
        # html = emoji.demojize(html)
        # cop = re.compile("[^\u0020-\u007e]")
        # html = cop.sub('',html)

        # selector = etree.HTML(html)
        # str = etree.tostring(selector)

        # return selector
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
                # print('Error:',e)
                # traceback.print_exc()

    def get_review_url_proc(self,review_request_queue):
        #construct urls
        #get attr's name,construct a new file of this attr(upper level)
        html = self.get_html(self.base_url.format(page=''))
        self.page_cnt = int(int(html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[11]/div[2]/div/div/text()[6]')[0].replace(',',''))/10)
        #first_page is diff url
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
        #base_url = 'https://www.tripadvisor.in/Attraction_Review-g186338-d553603-Reviews{page}-London_Eye-London_England.html'
        for i in range(self.page_cnt):
            #start from sec
            bias = (i+1)*10     #10,20...52900,52910
            url = self.base_url.format(page='-or'+str(bias))
            #url_list.append(url)
            review_request_queue.put(url)
            #single_page_proc(url,bias)
        self.GET_finish = True
        print("--------------GET_FINISH!!!---------------")

    def single_review_proc(self,review_url,review_get_queue):      
        html = self.get_html(review_url)
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
            review_get_queue.put(review)

    def use_review_url_proc(self,review_request_queue,review_get_queue):
        while 1:
            if(review_request_queue.empty() is True):
                #delay for get_url
                print("---------------use sleep---------------")
                time.sleep(1)
                if(review_request_queue.empty() is True):
                    if(self.GET_finish is True):
                        self.USE_finish = True
                        print("--------------use_FINISH!!!---------------")
                    else:
                        print("---------------use_closed-----------------")
                    self.flag = True
                    break
            else:
                url = review_request_queue.get()
                self.single_review_proc(url,review_get_queue)

    def write_to_file(self,review_get_queue,index_queue):
        while True:
            if(review_get_queue.empty() is True or index_queue.empty() is True):
                #delay for get_url
                print("---------------write sleep---------------")
                time.sleep(30)
                if(review_get_queue.empty() is True or index_queue.empty() is True):
                    if(self.USE_finish is True):
                        self.SAVE_finish = True
                        print("--------------write_FINISH!!!---------------")
                    else:
                        print("---------------closed---------------")
                    self.flag = True   
                    break
            else:
                idx = index_queue.get()
                index_queue.put(idx+1)
                reviews = {}
                for i in range(self.max_review):
                    # reviews.update(review)
                    id = idx*self.max_review+i
                    if(review_get_queue.empty() is False):
                        review = review_get_queue.get()
                        reviews[id] = review
                    else:
                        break
                lock = threading.Lock()
                lock.acquire()
                path = self.save_path.format(attr_name=self.attr_name,index=idx)
                print(path+"\n")
                print("---------------------------\n")
                f = open(path,"a")
                json.dump(reviews,f,indent=2)
                lock.release()

    def check_get(self,sleeptimes,get_initThreadName=[]):
        while True:
            if(self.GET_finish is True):
                break
            nowThreasName=[]
            now = threading.enumerate()
            for i in now:
                nowThreasName.append(i.getName())
            for thread in get_initThreadName:
                if thread in nowThreasName:
                    pass
                else:
                    print("restart"+thread+'\n')
                    get_url_thread = threading.Thread(target=self.get_review_url_proc,args=(self.review_request_queue,))
                    get_url_thread.daemon =True
                    get_url_thread.setName(thread)
                    get_url_thread.start()
            time.sleep(sleeptimes)
            
    def check_use(self,sleeptimes,use_initThreadName=[]):
        while True:
            if(self.USE_finish is True):
                break
            nowThreasName=[]
            now = threading.enumerate()
            for i in now:
                nowThreasName.append(i.getName())
            for thread in use_initThreadName:
                if thread in nowThreasName:
                    pass
                else:
                    print("restart"+thread+'\n')
                use_url_thread = threading.Thread(target=self.use_review_url_proc,args=(self.review_request_queue,self.review_get_queue,))
                use_url_thread.daemon = True
                use_url_thread.setName(thread)
                use_url_thread.start()
            time.sleep(sleeptimes)

    def check_save(self,sleeptimes,save_initThreadName=[]):
        while True:
            if(self.SAVE_finish is True):
                break
            nowThreasName=[]
            now = threading.enumerate()
            for i in now:
                nowThreasName.append(i.getName())
            for thread in save_initThreadName:
                if thread in nowThreasName:
                    pass
                else:
                    print("restart"+thread+'\n')
                save_thread = threading.Thread(target=self.write_to_file,args=(self.review_get_queue,self.index_queue))
                save_thread.daemon = True
                save_thread.setName(thread)
                save_thread.start()
            time.sleep(sleeptimes)
    def main(self):
        # review_request_queue = Queue()
        # review_get_queue = Queue()
        # index_queue = Queue()
        self.index_queue.put(0)
        review_generate_dict = []

        thread_pool = []
        get_initThreadName = []
        use_initThreadName = []
        save_initThreadName = []

        #generate reveiw urls
        for i in range(1):
            get_url_thread = threading.Thread(target=self.get_review_url_proc,args=(self.review_request_queue,))
            get_url_thread.daemon =True
            thread_name = 'get_url_{index}'.format(index=i)
            get_url_thread.setName(thread_name)
            get_url_thread.start()
            thread_pool.append(get_url_thread)
            get_initThreadName.append(get_url_thread.getName())

        #crawl review url
        time.sleep(2)
        for i in range(10):
            use_url_thread = threading.Thread(target=self.use_review_url_proc,args=(self.review_request_queue,self.review_get_queue,))
            use_url_thread.daemon = True
            thread_name = 'use_url_{index}'.format(index=i)
            use_url_thread.setName(thread_name)
            use_url_thread.start()
            thread_pool.append(use_url_thread)
            use_initThreadName.append(use_url_thread.getName())
        
        #save to file
        time.sleep(10)
        for i  in range(3):
            save_thread = threading.Thread(target=self.write_to_file,args=(self.review_get_queue,self.index_queue))
            save_thread.daemon = True
            thread_name = 'save_{index}'.format(index=i)
            save_thread.setName(thread_name)
            save_thread.start()
            thread_pool.append(save_thread)
            save_initThreadName.append(save_thread.getName())
        
        # init = threading.enumerate()
        # for i in init:
        #     initThreadName.append(i.getName())


        check_get = threading.Thread(target=self.check_get,args=(600,get_initThreadName,))
        check_get.setName('check-GET')
        check_get.start()
        thread_pool.append(check_get)
        
        check_use = threading.Thread(target=self.check_use,args=(180,use_initThreadName,))
        check_use.setName('check-USE')
        check_use.start()
        thread_pool.append(check_use)

        check_save = threading.Thread(target=self.check_save,args=(60,save_initThreadName,))
        check_save.setName('check-SAVE')
        check_save.start()
        thread_pool.append(check_save)

        for thread in thread_pool:
            thread.join()


        print("threads end!")

start = time.time()

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('Spider.log')
formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

start_url_2 = 'https://www.tripadvisor.in/Attraction_Review-g186338-d553603-Reviews{page}-London_Eye-London_England.html'
start_url = 'https://www.tripadvisor.in/Attraction_Review-g186338-d194299-Reviews{page}-Churchill_War_Rooms-London_England.html'
urls = []
urls.append('https://www.tripadvisor.in/Attraction_Review-g186338-d211708-Reviews{page}-Houses_of_Parliament-London_England.html')
urls.append('https://www.tripadvisor.in/Attraction_Review-g186338-d211709-Reviews{page}-Big_Ben-London_England.html')
urls.append('https://www.tripadvisor.in/Attraction_Review-g186338-d218015-Reviews{page}-Westminster-London_England.html')


# a = AT_view_spider(urls[0])
# a.main()

a = AT_view_spider(start_url)
a.main()

# sp = []
# for url in urls:
#     s = AT_view_spider(url)
#     sp.append(s)
# run_thread_pool = []
# for s in sp:
#     run_thread = threading.Thread(target=s.main(),args=())
#     run_thread.start()
#     run_thread_pool.append(run_thread)
# for thread in run_thread_pool:
#     thread.join()

end = time.time()
print("time:%s" %(end-start))
#todo folder create