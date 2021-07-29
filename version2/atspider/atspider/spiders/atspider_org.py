from __future__ import absolute_import
import scrapy
from scrapy import selector
from scrapy.http import HtmlResponse, request
from scrapy.http.response import Response
from scrapy.selector import Selector
import emoji
import re
import logging
import time
import sqlite3
import requests
import traceback
from lxml import etree
from atspider.items import AtspiderItem
# from items import AtspiderItem
# import items
class atspider_org(scrapy.Spider):
    name = "atspider_org"
    start_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-a_allAttractions.true-London_England.html'
    base_url_0 = 'https://www.tripadvisor.in/Attraction_Review-g186338-d189033-Reviews{page}-Little_Venice-London_England.html'
    base_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-oa{}-London_England.html'
    region = 'London_England'
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    handler = logging.FileHandler('AT_Spider.log')
    formatter = logging.Formatter('%(asctime)s - %(lineno)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def start_requests(self):
        self.logger.info("start time: %s" %str(time.time()))
        # home = 'https://www.tripadvisor.in/Attraction_Review-g186338-d187531-Reviews-Notting_Hill-London_England.html'
        # yield scrapy.Request(home, callback=self.parseHome)
        region = 'https://www.tripadvisor.in/Attractions-g186338-Activities-oa270-London_England.html'
        yield scrapy.Request(region, callback=self.parseRegion)

        # try:
        #     response = requests.get(region)
        #     response = self.modiResponse(response)
        #     selector = etree.HTML(response.text)
        #     page_cnt = int(int(selector.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[6]')[0].replace(',',''))/30)
        #     print("\033[5;36;40m----------------------page:%d-------------------次\033[;;m"%page_cnt)

        #     for i in range(page_cnt):
        #         attr_url = self.base_url.format(i*30)
        #         yield scrapy.Request(attr_url,callback=self.parseAttrPage)
        # except Exception as e:
        #     self.logger.error(e)  
    
    #function:beautify response
    def modiResponse(self,response):
        response = response.text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        response = emoji.demojize(response)
        cop = re.compile("[^\u0020-\u007e]")
        response = cop.sub('',response)
        return response
    #function:customize get html
    def get_html(self,url):
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71'}
        html = requests.get(url,headers = header).text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        
        html = emoji.demojize(html)
        cop = re.compile("[^\u0020-\u007e]")
        html = cop.sub('',html)

        selector = etree.HTML(html)
        str = etree.tostring(selector)

        return selector
    #function:construct attractions URL and database
    def parseRegion(self,response):
        try:
            ## test
            start_page = self.get_html(self.start_url)
            cnt = int(int(start_page.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[6]')[0].replace(',',''))/30)
            self.logger.info("page_cnt is %d" %cnt)

            response = self.modiResponse(response)
            selector = etree.HTML(response)
            page_cnt = selector.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[1]')
            # print("\033[5;36;40m----------------------page:%d-------------------次\033[;;m"%page_cnt)
            
            for i in range(50,100):
                attr_url = self.base_url.format(i*30)
                yield scrapy.Request(attr_url,callback=self.parseAttrPage)
        except Exception as e:
            self.logger.error(e) 
            self.logger.error(traceback.format_exc())       
    #function:get all attrs url in AttrPage and insert data into db
    def parseAttrPage(self,response):
        try:
            response = self.modiResponse(response)
            html = etree.HTML(response)
            attrs_url = html.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]//section[@class="_3Y-YU9SE _2gl5HHyP"]//div[@class="_1R2M9xFP"]//a/@href')
            #index !!!
            for i in range(len(attrs_url)):
                attrs_url[i] = str(attrs_url[i])
                attrs_url[i] = 'https://www.tripadvisor.in'+attrs_url[i]
                yield scrapy.Request(attrs_url[i],callback=self.parseAttrInfo)

            # page_cnt = int(int(html.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[6]')[0].replace(',',''))/30)
            # for i in range(self.page_cnt):
            #     attr_url = self.base_url.format(i*30)
            #     yield scrapy.Request(attr_url,callback=self.parseAttrPage)
        except Exception as e:
            self.logger.error(e)      
            self.logger.error(traceback.format_exc())       
    #function: get Attr Info
    def parseAttrInfo(self,response):
        try:
            response = self.modiResponse(response)
            html = etree.HTML(response)

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
            attraction['location'] = location
            attraction['labels'] = keywords
            attraction['score'] = score
            attraction['score_cnt'] = score_cnt
            attraction['experiences'] = experience
            attraction['nearby'] = nearby

            at_item = AtspiderItem()
            at_item['attr_name'] = name
            at_item['attr_info'] = attraction
            yield at_item
        except Exception as e:
            self.logger.error(e)  
            self.logger.error(traceback.format_exc())  
    #function: construct review url
    def parseHome(self, response):
        try:
            response = self.modiResponse(response)
            selector = etree.HTML(response)
            page_cnt = int(int(selector.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[11]/div[2]/div/div/text()[6]')[0].replace(',',''))/10)
            self.logger.info("total page of attr is %d" %page_cnt)
            for i in range(-1,page_cnt):
                #start from sec
                bias = (i+1)*10     #10,20...52900,52910
                url = self.base_url_0.format(page='-or'+str(bias))
                yield scrapy.Request(url, callback=lambda response,page=i,url=url :self.parseReviewPage(response,page,url))
        except Exception as e:
            self.logger(e)
    #function: parse 10 reviews in a review page
    def parseReviewPage(self,response,page,url):
        try:
            page_cnt = int(int(re.findall("\d+",url)[2])/10)    # 输出结果为列表
            print(page_cnt)
            self.logger.info("page is %d" %page_cnt)

            response = self.modiResponse(response)
            html = etree.HTML(response)
            review_dict = {}
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
                for res in re_body:
                    res = res.encode('utf-8').decode('utf-8')
                    reviews += res

                review['title'] = re_title
                review['time'] = re_time
                review['type'] = re_type
                review['review'] = reviews
                # print(re_title)  
                review_dict[page_cnt*10+i] = review
            at_item = AtspiderItem()
            at_item['attr_page'] = page_cnt
            at_item['attr_reviews'] = review_dict
            
            yield at_item
        except Exception as e:
            self.logger.error(e)


    def parseForum(self, response):
        urls = response.css(
            'table#SHOW_FORUMS_TABLE tr b a::attr(href)').getall()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        def parsepost(selector):
            return {
                'username': selector.css('div.profile span::text').get(),
                'posttime': selector.css('div.postDate::text').get(),
                'posttext': selector.css('div.postBody p::text').getall(),
            }
        yield {
            'topic': response.css('div#headingWrapper h1::text').get(),
            'page': response.css('div.deckTools span.pageDisplay::text').get(),
            'firstpost': parsepost(response.css('div.firstPostBox')),
            'replypost': [parsepost(replypost) for replypost in response.css('div.post')][1:],
        }

        nextpage = response.css(
            'div.deckTools a.sprite-pageNext::attr(href)').get()
        if nextpage is not None:
            nextpage = response.urljoin(nextpage)
            yield scrapy.Request(nextpage, callback=self.parse)
