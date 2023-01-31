#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    tune.py
    Get metadata from tvmaze
"""

import os, sys
from .utils import get_json
import bs4 as BeautifulSoup
from simplecache import use_cache
import json

class TVMaze(object):
    """Music from TVMaze """

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
    def get_tvmaze(self, imdb_id):
        params = imdb_id
        data = self.get_data(params)
        return self.map_details(data) if data else None
 
    @use_cache(60) 
    def get_data(self, params):
        """helper method to get data from rt  API"""
        base_url = 'https://api.tvmaze.com/lookup/shows?imdb=%s' % (params)
        return get_json(base_url)

    @staticmethod
    def map_details(data):
        """helper method to map the details received from tvmaze to kodi compatible format"""
        result = {}
        result["status"] = data["status"]
        if "rating" in data:
            result["rating.tvmaze"] = data["rating"].get("average")
        return result                