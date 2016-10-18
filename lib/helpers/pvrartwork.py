#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import log_msg, get_json, KODI_LANGUAGE
from operator import itemgetter
from simplecache import SimpleCache
import xbmc, xbmcgui
from tmdb import Tmdb
from fanarttv import FanartTv
from google import GoogleImages
import kodidb


class PvrArtwork(object):
    '''get artwork for kodi pvr'''
    
    custom_lookup_path = ""
    ignore_titles = []
    ignore_channels = []
    enable_online_lookup = True
    enable_google_lookup = True
    
    def __init__(self):
        self.kodi_db = kodidb.KodiDb()
        self.tmdb = Tmdb()
        self.cache = SimpleCache()
        self.fanarttv = FanartTv()
        self.google = GoogleImages()
    
    def get_pvr_artwork(self, title, channel="", year="", genre="", manual_lookup=False, ignore_cache=False):
        '''
            collect full metadata and artwork for pvr entries
            parameters: title (required)
            channel: channel name (optional)
            year: year or date (optional)
            genre: (optional)
            the more optional parameters are supplied, the better the search results
        '''
        
        #guess media type for better matching
        if "movie" in genre.lower():
            details["media_type"] = "movie"
        elif "tv" in genre.lower():
            details["media_type"] = "tvshow"
        elif "serie" in genre.lower():
            details["media_type"] = "tvshow"
        else:
            details["media_type"] = ""
        
        #grab from cache first
        cache_str = "SkinHelper.PvrArtwork.%s.%s.%s.%s"%(title,channel,year,genre)
        cache = cache.get(cache_str)
        if cache and not manual_lookup and not ignore_cache:
            return cache
            
        #no data in cache - initiate lookup
        details = {}
        details["pvrtitle"] = title
        details["pvrchannel"] = channel
        details["genre"] = genre
        details["year"] = year
        
        #only continue if we pass our basic checks
        if self.pvr_proceed_lookup() and not manual_lookup:
            
            #if manual lookup get the title from the user
            if manual_lookup:
                dialog = xbmcgui.Dialog()
                searchtitle = dialog.input(xbmc.getLocalizedString(16017), title, type=xbmcgui.INPUT_ALPHANUM).decode("utf-8")
                if not searchtitle:
                    return
            else:
                searchtitle = get_searchtitle(title,channel)
            
            #lookup recordings database
            details.update( self.lookup_local_recordings(title) )
            
            #lookup custom path
            details.update( self.lookup_custom_path(searchtitle, title) )
            
            #lookup movie/tv library
            details.update( self.lookup_local_library(searchtitle, details["media_type"]) )
            
            #do internet scraping
            if enable_online_lookup:
                
                #tmdb scraping
                if details["media_type"] == "movie":
                    details.update( self.tmdb.search_movie(searchtitle, year, manual_lookup) )
                elif details["media_type"] == "tvshow":
                    details.update( self.tmdb.search_tvshow(searchtitle, year, manual_lookup) )
                else:
                    details.update( self.tmdb.search_video(searchtitle, year, manual_lookup) )
                
                #fanart.tv scraping
                if not details.get("art"):
                    details["art"] = {}
                if details.get("imdbnumber") and details["media_type"] == "movie":
                    details["art"] = fanarttv.movie(details["imdbnumber"])
                elif details.get("tvdb_id") and details["media_type"] == "tvshow":
                    details["art"] = fanarttv.tvshow(details["tvdb_id"])
                    
                #optional google thumb
                if enable_google_lookup and not details.get("thumbnail") and not details.get("art"):
                    details["thumbnail"] = google.search_image(searchtitle,manual_lookup)
                    
        self.cache.set(cachestr,details)
        return details
               
    def pvr_proceed_lookup(self, title, channel):
        '''perform some checks if we can proceed with the lookup'''
        if title in self.ignore_titles:
            return False
        if title.lower() in self.ignore_titles:
            return False
        if channel.lower() in self.ignore_channels:
            return False
        if not title:
            return False
        return True
        
    def get_searchtitle(self, title, channel):
        if not isinstance(title, unicode):
            title = title.decode("utf-8")
        title = title.lower()
        #split characters - add common splitters
        for splitchar in [": "," ("," %s"%channel.lower()]:
            if splitchar.lower() in title:
                title = title.split(splitchar)[0]
        #replace common chars and words
        for char in [".", "'", "`", "_new", "new_"," %s"%channel.lower()]:
            title = title.replace(char,"")
        for char in ["_","_","`"]:
            title = title.replace(char," ")
        return title
    
    def lookup_local_recordings(self, title):
        '''lookup actual recordings to get details for grouped recordings
           also grab a thumb provided by the pvr
        '''
        details = {}
        json_query = self.kodi_db.recordings(sort=kodidb.SORT_DATEADDED, 
            filter={"field": "title", "operator": "contains", "value": title})
        for item in json_query:
            if not channel:
                details["channel"] = item["channel"]
            if not genre:
                details["genre"] = " / ".join(item["genre"])
            if item.get("art"):
                details["thumbnail"] = item["art"].get("thumbnail")
        if len(json_query) > 1:
            details["media_type"] == "tvshow"
        return details
            
    def lookup_custom_path(self, searchtitle, title):
        details = {}
        if self.custom_lookup_path:
            pass #TODO
        return details
        
    def lookup_local_library(self, title, media_type):
        details = {}
        filters = [{"operator":"is", "field":"title","value":title}]
        if not media_type or media_type == "tvshow":
            kodi_items = self.kodi_db.tvshows(filters=filters,limits=(0,1))
            if kodi_items:
                details = kodi_items[0]
                details["media-type"] = "tvshow"
        if not details and (not media_type or media_type == "movie"):
            kodi_items = self.kodi_db.movies(filters=filters,limits=(0,1))
            if kodi_items:
                details = kodi_items[0]
                details["media-type"] = "movie"
        return details
        
    
 