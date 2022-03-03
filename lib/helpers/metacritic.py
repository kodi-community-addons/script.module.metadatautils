#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    Metacritic.py
    Get metadata from Metacritic
"""

import os, sys
from .utils import get_json, requests, try_parse_int, log_msg
import bs4 as BeautifulSoup
from simplecache import use_cache
import json

class Metacritic(object):
    """Info from Metacritic (currently only top250)"""

    def __init__(self, simplecache=None, kodidb=None):
        """Initialize - optionaly provide simplecache object"""
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
        if not kodidb:
            if sys.version_info.major == 3:
                from .kodidb import KodiDb
            else:
                from kodidb import KodiDb
            self.kodidb = KodiDb()
        else:
            self.kodidb = kodidb

    @use_cache(2)        
    def get_metacritic(self, title):
        title = title.replace(" ", "-").lower()
        headers = {'User-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows Phone OS 7.0; Trident/3.1; \
            IEMobile/7.0; LG; GW910)'}
        html = ''
        url = "https://www.metacritic.com/tv/%s" % title
        html = requests.get('https://www.metacritic.com/tv/%s' % title, headers=headers, timeout=15)
        soup = BeautifulSoup.BeautifulSoup(html.text, features="html.parser")
        #for div in soup.find_all("a", class="metascore_anchor"):
            #result["metacritic.userscore"] = div.get("span")
        for div in soup.find_all("script", type="application/ld+json"):
            for mcc in div:
                data = json.loads(mcc)
                #log_msg("get_metacritic_all - data from json %s -%s" %  (title, data))
                if data:        
                    return self.map_details(data) if data else None

    @staticmethod
    def map_details(data):
        """helper method to map the details received from metacritic to kodi compatible format"""
        result = {}
        if sys.version_info.major == 3:
            for key, value in data.items():
                # filter the N/A values
                if value in ["N/A", "NA"] or not value:
                    continue
                if key == "name":
                    result["title.mc"] = value
                elif key == "description":
                    result["description.mc"] = value
                if data.get("aggregateRating"):
                    if data["aggregateRating"].get("ratingValue"):
                        result["metacritic.rating"] = data["aggregateRating"].get("ratingValue")
                    if data["aggregateRating"].get("ratingCount"):
                        result["metacritic.votes"] = data["aggregateRating"].get("ratingCount")
                if data.get("trailer"):
                    if data["trailer"].get("thumbnailUrl"):
                        result["metacritic.thumb"] = data["trailer"].get("thumbnailUrl")        
        return result
                    