from __future__ import absolute_import
import scrapy
from scrapy import selector
from scrapy.http import HtmlResponse
from scrapy.selector import Selector
import emoji
import re
from lxml import etree
from atspider.items import AtspiderItem
# from items import AtspiderItem
# import items
class atspider_org(scrapy.Spider):
    name = "atspider_org"
    base_url = 'https://www.tripadvisor.in/Attraction_Review-g186338-d218015-Reviews{page}-Westminster-London_England.html'
    def start_requests(self):
        #if else
        home = 'https://www.tripadvisor.in/Attraction_Review-g186338-d218015-Reviews-Westminster-London_England.html'
        yield scrapy.Request(home, callback=self.parseHome)
    
    #function:beautify response
    def modiResponse(self,response):
        response = response.text.replace('<!--red_beg-->','').replace('<!--red_end-->','').replace('<em>','').replace('</em>','')
        response = emoji.demojize(response)
        cop = re.compile("[^\u0020-\u007e]")
        response = cop.sub('',response)
        return response

    #function: construct review url
    def parseHome(self, response):
        response = self.modiResponse(response)
        selector = etree.HTML(response)
        page_cnt = int(int(selector.xpath('//*[@id="tab-data-qa-reviews-0"]/div/div[5]/div[11]/div[2]/div/div/text()[6]')[0].replace(',',''))/10)
        for i in range(-1,page_cnt):
            #start from sec
            bias = (i+1)*10     #10,20...52900,52910
            url = self.base_url.format(page='-or'+str(bias))
            yield scrapy.Request(url, callback=lambda response,page=i :self.parseReviewPage(response,page))
    #function: parse 10 reviews in a review page
    def parseReviewPage(self,response,page):
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
            for re in re_body:
                re = re.encode('utf-8').decode('utf-8')
                reviews += re

            review['title'] = re_title
            review['time'] = re_time
            review['type'] = re_type
            review['review'] = reviews
            # print(re_title)  
            review_dict[page*10+i] = review
        at_item = AtspiderItem()
        at_item['attr_page'] = page
        at_item['attr_reviews'] = review_dict
        
        # print("\033[5;36;40m----------------------请求成功----------------page-%d\033[;;m"%page)
        yield at_item
        # urls = response.css(
        #     'table.forumtopic tr td.fname a::attr(href)').getall()
        # for url in urls:
        #     print(url)
        #     yield scrapy.Request(url, callback=self.parseForum)

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
