import queue
import threading
from queue import Queue
import time
from lxml import etree
import requests

import traceback
import emoji
import requests
import json
import re

class AT_spider:
    def __init__(self,start_url):
        self.start_url = start_url
        self.page_cnt = 0
        self.url_list = []
        self.attr_list = []
        self.flag = False
        self.page_flag = False
        self.end = False

    def get_html(self,url):
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
        html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        
        html = emoji.demojize(html)
        cop = re.compile("[^\u0020-\u007e]")
        html = cop.sub('',html)

        selector = etree.HTML(html)
        str = etree.tostring(selector)

        return selector

    def get_raw_html(self,url):
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
        html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        return html

    def get_attr_url(self,city_url):
        html = self.get_html(city_url)
        attrs_url = html.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]//section[@class="_3Y-YU9SE _2gl5HHyP"]//div[@class="_1R2M9xFP"]//a/@href')
        for i in range(len(attrs_url)):
            attrs_url[i] = str(attrs_url[i])
            attrs_url[i] = 'https://www.tripadvisor.in'+attrs_url[i]
            #f.write(attrs_url[i]+"\n")
        #f.close()
        return attrs_url

    def get_attr_info(self,attr_queue):
         while 1:
            if(attr_queue.empty() is True):
                #delay for get_url
                time.sleep(10)
                if(attr_queue.empty() is True):
                    self.flag = True
                    print("---------------closed---------------")
                    break
            else:
    
                attr_url = attr_queue.get()
                html = self.get_html(attr_url)
                print("---------------enter---------------")

                ##name
                name = html.xpath('//*[@id="lithium-root"]/main/div[1]/div[2]/div[1]/header/div[3]/div[1]/div/h1//text()')[0]
                cop = re.compile("['/','?',':','*','<','>','|',\u0022]")    #todo:'\'
                name = cop.sub("",name)

                print("name:%s" %name)

                ##labels
                keywords = html.xpath('//*[@id="lithium-root"]/main/div[1]/div[2]/div[2]/div/div/span/section[1]/div/div/span/div/div[1]/div[3]/div/text()')
                keywords = re.split('&',keywords[0])
                keywordslists = html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[1]/div/div[3]/div[2]/*//text()')
                keywords.extend(keywordslists)
                ##location
                location = html.xpath('//*[@id="tab-data-AppPresentation_PoiLocationSectionGroup"]/div/div/div[2]/div[1]/span/div/div/div[1]/button/span/text()')
                ##score&score cnt
                score = html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[3]/div[1]/div[1]/div[1]/text()')[0]
                score_cnt = html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[3]/div[1]/div[1]/div[2]/span/text()')  #to int
                cop = re.compile("[^0-9]")
                score_cnt = cop.sub('',score_cnt[0])
                ##nearby: hotels,restaurants
                # near_hotels = html.xpath('//*[@id="answer_faq_5"]/div/div/ul//a/text()')
                near_restas = html.xpath('//*[@id="tab-data-AppPresentation_PoiLocationSectionGroup"]/div/div/div[2]/div[3]/span[1]/div[4]//div[@class="DrjyGw-P NGv7A1lw _2yS548m8 _2cnjB3re _1TAWSgm1 _1Z1zA2gh _2-K8UW3T _2nPM5Opx"]//text()')
                near_attras = html.xpath('//*[@id="tab-data-AppPresentation_PoiLocationSectionGroup"]/div/div/div[2]/div[3]/span[2]/div[4]//div[@class="DrjyGw-P NGv7A1lw _2yS548m8 _2cnjB3re _1TAWSgm1 _1Z1zA2gh _2-K8UW3T _2nPM5Opx"]//text()')
                ##top ways to experience
                #names
                ex_names = html.xpath('//*[@id="lithium-root"]/main/div[1]/div[2]/div[2]/div/div/span/section[3]/div/div/span/div[2]//span[@class="DrjyGw-P _2AAjjcx8"]/text()')
                extype_cnt = len(ex_names)
                ex = ['']*extype_cnt
                for i in range(extype_cnt):
                    ex[i] = html.xpath('//*[@id="ATTRACTION_WAYS_TO_EXPERIENCE-tabpanel-{index}"]//li//div[@class="VQlgmkyI WullykOU _3WoyIIcL"]//text()'.format(index=i))

                experience = {}
                for i in range(extype_cnt):
                    experience[ex_names[i]] = ex[i]
                nearby = {}
                # nearby['near_hotels'] = near_hotels
                nearby['near_restas'] = near_restas
                nearby['near_attras'] = near_attras

                #turn to json
                attraction = {}
                attraction['name'] = name
                attraction['labels'] = keywords
                attraction['score'] = score
                attraction['score_cnt'] = score_cnt
                attraction['experiences'] = experience
                attraction['nearby'] = nearby

                lock = threading.Lock()
                lock.acquire()
                path = "C:\\Users\\t-dohuang\\source\\repos\\TripAdvisor_spi\\London_data\\reletive_info\\{}.json".format(name)
                f = open(path,"a")
                json.dump(attraction,f,indent=2)  
                lock.release()               

    def use_url(self,url_queue,attr_queue):
        time.sleep(0.1)
        while 1:
            if(url_queue.empty() is True):
                #delay for get_url
                time.sleep(1)
                if(url_queue.empty() is True):
                    self.page_flag = True
                    print("---------------use_closed---------------")
                    break
            else:
                url = url_queue.get()
                # print("取得URL：{}\n".format(url))
                attrs_url = self.get_attr_url(url)
                for attr_url in attrs_url:
                    attr_queue.put(attr_url)
                    # print(attr_url+"\n")
                  

        
    def get_url(self,url_queue):
        base_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-a_allAttractions.true-London_England.html'
        # html = get_html(base_url)

        # 构造所有ｕｒｌ    todo:10-->page_cnt
        for i in range(self.page_cnt):
            attr_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-oa{}-London_England.html'.format(i*30)
            url_queue.put(attr_url)
            # print("获得URL：{}".format(attr_url))    


    def main(self):
        start_page = self.get_html(self.start_url)
        self.page_cnt = int(int(start_page.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[6]')[0].replace(',',''))/30)
        
        thread_pool = []
        res_queue = Queue()
        out_queue = Queue()
        get_url_thread = threading.Thread(target=self.get_url,args=(res_queue,))
        get_url_thread.daemon = True
        get_url_thread.start()
        # get_url_thread.join()
        # time.sleep(15)
        for i in range(5):
            use_url_thread = threading.Thread(target=self.use_url,args=(res_queue,out_queue,))
            use_url_thread.daemon = True
            use_url_thread.start()
            thread_pool.append(use_url_thread)
        
        time.sleep(30)
        for i in range(10):
            get_attr_thread = threading.Thread(target=self.get_attr_info,args=(out_queue,))
            get_attr_thread.daemon = True
            get_attr_thread.start()
            thread_pool.append(get_attr_thread)

        for thread in thread_pool:
            thread.join()    

        # while 1:
        #     # print(self.flag)
        #     if self.end == True:
        #         break
        print("threads end!!!")

# def storage_url(stor_queue):
#     while(stor_queue.empty)

start = time.time()
start_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-a_allAttractions.true-London_England.html'
a = AT_spider(start_url)
a.main()
end = time.time()
print("time:%s" %(end-start))
