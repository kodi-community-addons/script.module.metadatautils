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
            from .kodidb import KodiDb
            self.kodidb = KodiDb()
        else:
            self.kodidb = kodidb

    @use_cache(2)        
    def get_metacritic(self, title, content_type):
        for splitter in [" ", " :",": ", ":"]:
            # replace splitter by kodi default splitter for easier split all later
            title = title.replace(splitter, "-").lower()
            for remover in ['(', ')']:
                title = title.replace(remover, "")
                title = title.replace("--", "-")
        if "movies" in content_type:
            content = ("movie/%s" %  title)
        if "tvshows" in content_type:
            content = ("tv/%s" %  title)
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'}
        html = ''
        html = requests.get('https://www.metacritic.com/%s' % content, headers=headers, timeout=15).text
        soup = BeautifulSoup.BeautifulSoup(html, features="html.parser")
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
                    