#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import requests, timedelta
import BeautifulSoup
import simplecache

class Imdb(object):
    '''Info from IMDB (currently only top250)'''
    top250_db = None
    
    def get_top250_rating(self,imdb_id):
        '''get the top250 rating for the given imdbid'''
        return self.get_top250_db().get(imdb_id,None)
    
    def get_top250_db(self):
        '''
            get the top250 listing for both movies and tvshows as dict with imdbid as key
            uses 7 day cache to prevent overloading the server
        '''
        #try cache first
        if self.top250_db:
            return self.top250_db
        cache_str = "SkinHelper.IMDB.Top250"
        cache = simplecache.get(cache_str)
        if cache:
            return cache
        #no cache - scrape both movies and tv listing and store results in dict
        results = {}
        for listing in [ ("top","chttp_tt_"),("toptv","chttvtp_tt_")]:
            html = requests.get("http://www.imdb.com/chart/%s"%listing[0], headers={'User-agent': 'Mozilla/5.0'}, timeout=20)
            soup = BeautifulSoup.BeautifulSoup(html.text)
            for table in soup.findAll('table'):
                if table.get("class") == "chart full-width":
                    for td in table.findAll('td'):
                        if td.get("class") == "titleColumn":
                            a = td.find("a")
                            if a:
                                url = a["href"]
                                imdb_id = url.split("/")[2]
                                imdb_rank = url.split(listing[1])[1]
                                results[imdb_id] = int(imdb_rank)
        #store in cache and return results
        simplecache.set(cache_str,results,expiration=timedelta(days=7))
        self.top250_db = results
        return results
    