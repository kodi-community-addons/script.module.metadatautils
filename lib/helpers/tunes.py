#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    tune.py
    Get metadata from TuneFind
"""

import os, sys
from .utils import get_json, log_msg
import bs4 as BeautifulSoup
from simplecache import use_cache
import json

class Tunes(object):
    """Music from Tunes """

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
    def get_tunes(self, title, media_type="", year=""):
        for splitter in [" ", " :",": ", ":"]:
            # replace splitter by kodi default splitter for easier split all later
            title = title.replace(splitter, "-").lower()
            for remover in ['(', ')']:
                title = title.replace(remover, "")
                title = title.replace("--", "-")
                title = title.replace(":-", "-")
                if "movies" in media_type:
                    params = "movie/%s-%s?fields=hot-songs" % (title, year)
                if "tvshows" in media_type:    
                    params = "show/%s/season/1?fields=hot-songs" % (title)
                data = self.get_data(params)
        return self.map_details(data) if data else None
 
    @use_cache(365) 
    def get_data(self, params):
        """helper method to get data from rt  API"""
        base_url = 'https://www.tunefind.com/api/frontend/%s' % (params)
        return get_json(base_url)

    @staticmethod
    def map_details(data):
        """helper method to map the details received from TuneFind to kodi compatible format"""
        result = {}
        for key, value in data.items():
                if data.get("hot_songs"):
                    videos:soundtrack = []
                    for count, item in enumerate(data["hot_songs"]):
                        videos:soundtrack.append(item["id"])
                        result["name.%s.soundtrack" % count] = item["name"]
                        result["track.%s.soundtrack" % count] = item["preview_url"]
                        s_thumb = ""
                        s_track = ""
                        if item.get("url"):
                            data = item["url"]
                            if data.get("external_art_url"):
                                s_thumb = data.get("external_art_url")
                            if data.get("external_preview_url"):
                                s_track = data.get("external_preview_url")
                        result["image.%s.soundtrack" % count] = s_thumb
                        result["track.%s.soundtrack" % count] = s_track              
        return result
                    