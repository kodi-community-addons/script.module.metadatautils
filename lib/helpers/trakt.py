#!/usr/bin/python
# -*- coding: utf-8 -*-

"""get metadata from trakt"""
import os, sys
from urllib.parse import urlencode
from .utils import get_json, get_xml, formatted_number, int_with_commas, try_parse_int, KODI_LANGUAGE, ADDON_ID, try_encode, log_msg
from simplecache import use_cache
import arrow
import xbmc
import xbmcaddon
import xbmcgui

BASE_URL = "https://api.trakt.tv/"

class Trakt(object):
    """get metadata from trakt"""
    api_key = None  # public var to be set by the calling addon
    def __init__(self, simplecache=None):
        """Initialize - optionaly provide simplecache object"""
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
        addon = xbmcaddon.Addon(id=ADDON_ID)
        api_key = addon.getSetting("traktapi_apikey")
        if api_key:
            self.api_key = api_key
        del addon

    @use_cache(14)
    def get_pvr_details_by_imdbid(self, imdb_id, content_type):
        """get trakt details by providing an imdb id"""
        if "movie" in content_type:
            content_type = "movies"
        elif content_type in ["tvshows", "tvshow", "tvchannels"]:
            content_type = "shows"
        params = '%s/%s?extended=full' % (content_type, imdb_id)
        data = self.get_data(params)
        return self.map_details(data) if data else None

    @use_cache(14)
    def get_details_by_imdbid(self, imdb_id, content_type):
        """get trakt details by providing an imdb id"""
        win = xbmcgui.Window(10000)
        content_type = win.getProperty("contenttype")
        if "movie" in content_type:
            content_type = "movies"
        elif content_type in ["tvshows", "tvshow", "tvchannels"]:
            content_type = "shows"
        params = '%s/%s?extended=full' % (content_type, imdb_id)
        data = self.get_data(params)
        return self.map_details(data) if data else None

    @use_cache(14)
    def get_data(self, params):
        """helper method to get data from trakt json API"""
        url = 'https://api.trakt.tv/%s' % params
        api_key = self.api_key
        HEADERS = {
            'Content-Type': 'application/json',
            'trakt-api-key': api_key,
            'trakt-api-version': "2"
            }
        return get_json(url, headers=HEADERS)
        
    @staticmethod                                   
    def map_details(data):
        """helper method to map the details received from trakt to kodi compatible format"""
        result = {}
        ytb_plgn = 'plugin://plugin.video.youtube/?action=play_video&videoid='
        if sys.version_info.major == 3:
            for key, value in data.items():
                # filter the N/A values
                if value in ["N/A", "None"] or not value:
                    continue
                if key == "title":
                    result["title"] = value
                elif key == "year":
                    try:
                        result["year"] = try_parse_int(value.split("-")[0])
                    except Exception:
                        result["year"] = value
                elif key == "genre":
                    result["genre"] = value.split(", ")
                elif key == "country":
                    result["country"] = value
                elif key == "votes":
                    result["votes.trakt"] = value
                elif key == "rating":
                    result["rating.trakt"] = value
                elif key == "trailer":
                    trakttr = value.split("=")[1]
                    result["trakt.trailer"] = '%s%s' % (ytb_plgn, trakttr)
                elif key == "country":
                    result["country"] = value
                elif key == "status":
                    result["status"] = value
                elif key == "overview":
                    result["trakt.plot"] = value
                elif key == "tagline":
                    result["trakt.tagline"] = value
                elif key == "aired_episodes":
                    result["aired.episodes"] = value
        return result