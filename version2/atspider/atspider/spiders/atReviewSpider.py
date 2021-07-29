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
from atspider.items import ReviewsItem

class atReviewSpider(scrapy.Spider):
    name = 'atReviewSpider'
    allowed_domains = ['tripadvisor.in/']
    start_urls = ['http://www.tripadvisor.in//']
    start_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-a_allAttractions.true-London_England.html'
    base_url = 'https://www.tripadvisor.in/Attractions-g186338-Activities-oa{}-London_England.html'

    def start_requests(self):
        region = 'https://www.tripadvisor.in/Attractions-g186338-Activities-oa270-London_England.html'
        yield scrapy.Request(region,callback=self.parseRegion)
    
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
            
            for i in range(101,110):
                attr_url = self.base_url.format(i*30)
                yield scrapy.Request(attr_url,callback=self.parseAttrPage,dont_filter=True)
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
                url = attrs_url[i]
                yield scrapy.Request(attrs_url[i],callback=lambda response,url=url:self.parseAttrInfo(response,url),dont_filter=True)
                # yield scrapy.Request(url, callback=lambda response,page=i,url=url :self.parseReviewPage(response,page,url))
            # page_cnt = int(int(html.xpath('//*[@id="lithium-root"]/main/span/div/div[2]/div/div/div/span/div/div[2]/div[2]/section[39]/span/div[2]/div/div/text()[6]')[0].replace(',',''))/30)
            # for i in range(self.page_cnt):
            #     attr_url = self.base_url.format(i*30)
            #     yield scrapy.Request(attr_url,callback=self.parseAttrPage)
        except Exception as e:
            self.logger.error(e)      
            self.logger.error(traceback.format_exc())  

    #function: get Attr Info
    def parseAttrInfo(self,response,attr_base_url):
        try:
            response = self.modiResponse(response)
            html = etree.HTML(response)
            attr_base_url = re.sub(r'(Reviews)',r'\1{page}',attr_base_url)
            print(attr_base_url)

            ##name
            name = html.xpath('//*[@id="lithium-root"]/main/div[1]/div[2]/div[1]/header/div[3]/div[1]/div/h1//text()')[0]
            cop = re.compile("['/','?',':','*','<','>','|',\u0022]")    #todo:'\'
            name = cop.sub("",name)

            #construct url for reviews page
            page_cnt = int(int(html.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[11]/div[2]/div/div/text()[6]')[0].replace(',',''))/10)
            self.logger.info("total page of attr is %d" %page_cnt)
            for i in range(-1,page_cnt):
                #start from sec
                bias = (i+1)*10     #10,20...52900,52910
                url = attr_base_url.format(page='-or'+str(bias))
                # print(url)
                yield scrapy.Request(url,callback=lambda response,attr_name=name,url=url,page_cnt=page_cnt :self.parseReviewPage(response,attr_name,url,page_cnt),dont_filter=True)
        except Exception as e:
            self.logger.error(e)  
            self.logger.error(traceback.format_exc())  

    #function: parse 10 reviews in a review page
    def parseReviewPage(self,response,attr_name,url,total_page_cnt):
        try:
            # attr_name = response.meta['attr_name']
            # url = response.meta['url']
            print("--------------------parseReviewPage------------------------called")
            page_cnt = int(int(re.findall("\d+",url)[2])/10)    # 输出结果为列表
            # print(page_cnt)
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
            at_item = ReviewsItem()
            at_item['attr_name'] = attr_name
            # at_item['attr_page_cnt'] = total_page_cnt
            at_item['attr_page'] = page_cnt
            at_item['attr_reviews'] = review_dict
            
            yield at_item
        except Exception as e:
            self.logger.error(e)
