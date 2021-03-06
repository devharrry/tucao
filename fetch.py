#-*- coding:utf-8 -*-
import urllib2
import json
import requests
import time
from news import News
from utils import *
from threading import Thread
from datetime import datetime


section = 2
sectionUrl = 'http://news-at.zhihu.com/api/2/section/' + str(section)
newsUrl = 'http://news-at.zhihu.com/api/2/news/'
beforeUlr = sectionUrl + '/before/'


class Fetch(Thread):

    def __get_news_from_api(self):
        news = News()
        news_ids_from_database = [news['news_id'] for news in news.list()]
        news_from_api = fetch_data(sectionUrl)['news']
        news_ids_from_api = [news['news_id'] for news in news_from_api]
        fetch_log('fetching')
        if news_ids_from_api[0] != news_ids_from_database[0]:
            fetch_log("detected new data from api")
            matched = [idx for idx, val in enumerate(news_ids_from_api) if val == news_ids_from_database[0]]
            if len(matched) == 0:
                end = len(news_ids_from_api)
            else:
                end = matched[0]
            fetch_log("end index is %s" %end)
            for news in news_from_api[:end][::-1]:
                self.__fetch_news(news)
        else:
            fetch_log('Nothing new')
        return None

    def __fetch_news(self, news_data):
        fetch_log('fetch news id %d' %(news_data['news_id']))
        data = fetch_data(newsUrl + str(news_data['news_id']))
        fetch_log('fetched news id %d' %(news_data['news_id']))
        if data is None or news_data['news_id'] != data['id']:
            return None
        data['body'] = parse_news_body(data['body'])
        fetch_log('parsed news body')
        try:
            data['image'] = upload_to_qiniu(data['image'])
        except KeyError:
            data['image'] = 'default-lg.jpg'
        fetch_log('image uploaded')
        data['thumbnail'] = upload_to_qiniu(news_data['thumbnail'])
        fetch_log('thumbnail uploaded')
        data['date'] = datetime.strptime(news_data['date'], '%Y%m%d')
        news = News(news_id=int(data['id']))
        news.save(data)
        fetch_log('news %s saved' % int(data['id']))
        return data['id']


    def init_fetch(self):
        print('fetching from api for the first time...')
        news_from_api = fetch_data(sectionUrl)['news']
        print('index data fetch finished')
        for news in news_from_api[::-1]:
            id = self.__fetch_news(news)
            print('news id %d fetched' %id)
        print('done')
        

    def run(self):
        while True:
            self.__get_news_from_api()
            time.sleep(60*60*2)

    

