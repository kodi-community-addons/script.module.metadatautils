#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, KODI_LANGUAGE, get_clean_image, DialogSelect
from operator import itemgetter
from simplecache import SimpleCache, use_cache
import xbmc, xbmcgui
from tmdb import Tmdb
from fanarttv import FanartTv
from google import GoogleImages
import kodidb
import re
from datetime import timedelta


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
    
    def get_pvr_artwork(self, title, channel, genre="", manual_select=False, ignore_cache=False):
        '''
            collect full metadata and artwork for pvr entries
            parameters: title (required)
            channel: channel name (required)
            year: year or date (optional)
            genre: (optional)
            the more optional parameters are supplied, the better the search results
        '''
        
        #try cache first
        cache_str = "pvr_artwork.%s.%s"%(title,channel)
        cache = self.cache.get(cache_str)
        if cache and not manual_select and not ignore_cache:
            return cache
            
        #no cache - start our lookup adventure    
        details = {}
        details["pvrtitle"] = title
        details["pvrchannel"] = channel
        details["genre"] = genre
        
        #guess media type for better matching
        if "movie" in genre.lower():
            details["media_type"] = "movie"
        elif "tv" in genre.lower():
            details["media_type"] = "tvshow"
        elif "serie" in genre.lower():
            details["media_type"] = "tvshow"
        else:
            details["media_type"] = ""
        
        #only continue if we pass our basic checks
        if self.pvr_proceed_lookup(title, channel):
            
            #if manual lookup get the title from the user
            if manual_select:
                dialog = xbmcgui.Dialog()
                searchtitle = dialog.input(xbmc.getLocalizedString(16017), title, type=xbmcgui.INPUT_ALPHANUM).decode("utf-8")
                if not searchtitle:
                    return
            else:
                searchtitle = self.get_searchtitle(title,channel)
            
            #lookup recordings database
            details.update( self.lookup_local_recordings(title) )
            
            #lookup custom path
            details.update( self.lookup_custom_path(searchtitle, title) )
            
            #lookup movie/tv library
            details.update( self.lookup_local_library(searchtitle, details["media_type"]) )
            
            #do internet scraping if results were not found in local db
            if self.enable_online_lookup and not details.get("art"):
                
                #tmdb scraping
                details.update( self.tmdb.search_video(searchtitle, preftype=details["media_type"], manual_select=manual_select) )
                
                if not details.get("art"):
                    details["art"] = {}
                
                #fanart.tv scraping
                if details.get("imdbnumber") and details["media_type"] == "movie":
                    details["art"].update(self.fanarttv.movie(details["imdbnumber"]))
                elif details.get("tvdb_id") and details["media_type"] == "tvshow":
                    details["art"].update(self.fanarttv.tvshow(details["tvdb_id"]))
                    
                #set thumb
                if details.get("thumbnail"):
                    thumb = details["thumbnail"]
                elif details["art"].get("landscape"):
                    thumb = details["art"]["landscape"]
                elif details["art"].get("fanart"):
                    thumb = details["art"]["fanart"]
                elif self.enable_google_lookup:
                    if manual_select:
                        google_title = searchtitle
                    else:
                        google_title = "%s + %s"%(searchtitle, channel.lower().split(" hd")[0])
                    thumb = self.google.search_image(google_title, manual_select)
                else:
                    thumb = ""
                details["thumbnail"] = thumb
                details["art"]["thumb"] = thumb
             
        self.cache.set(cache_str, details, expiration=timedelta(days=120))
                    
        return details
               
    def manual_set_pvr_artwork(self, title, channel, genre):
        '''manual override artwork options'''
        artwork = self.get_pvr_artwork(title, channel, genre)
        abort = False
        while not abort:
            listitems = []
            for art in ["thumb","poster","fanart","banner","clearart","clearlogo",
                "discart","landscape","characterart"]:
                listitem = xbmcgui.ListItem(label=art, iconImage=artwork.get(art,""))
                listitem.setProperty("icon",artwork.get(art,""))
                listitems.append(listitem)
            w = DialogSelect( "DialogSelect.xml", "", listing=listitems, 
                windowtitle=xbmc.getLocalizedString(13511),multiselect=False )
            w.doModal()
            selected_item = w.result
            if selected_item == -1:
                abort = True
            else:
                artoptions = []
                selected_item = listitems[selected_item]
                image = selected_item.getProperty("icon")
                label = selected_item.getLabel()
                heading = "%s: %s" %(xbmc.getLocalizedString(13511),label)
                if image:
                    listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(13512))
                    listitem.setProperty("icon",image)
                    artoptions.append(listitem)

                    listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(231))
                    listitem.setProperty("icon","DefaultAddonNone.png")
                    artoptions.append(listitem)

                listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(1024))
                listitem.setProperty("icon","DefaultFolder.png")
                artoptions.append(listitem)

                w2 = DialogSelect( "DialogSelect.xml", "", listing=artoptions, windowtitle=heading )
                w2.doModal()
                selected_item = w2.result
                if image and selected_item == 1:
                    artwork[label] = ""
                elif (image and selected_item == 2) or not image and selected_item == 0:
                    #manual browse...
                    image = xbmcgui.Dialog().browse( 2 , xbmc.getLocalizedString(1030), 
                        'files', mask='.gif|.png|.jpg').decode("utf-8")
                    if image:
                        artwork[label] = image            
        #save results in cache
        self.cache.set(cache_str, details, expiration=timedelta(days=120))
    
    def pvr_proceed_lookup(self, title, channel):
        '''perform some checks if we can proceed with the lookup'''
        if title in self.ignore_titles:
            return False
        if title.lower() in self.ignore_titles:
            return False
        if channel.lower() in self.ignore_channels:
            return False
        if not title or not channel:
            return False
        return True
        
    def get_searchtitle(self, title, channel):
        '''common logic to get a proper searchtitle from crappy titles provided by pvr'''
        if not isinstance(title, unicode):
            title = title.decode("utf-8")
        title = title.lower()
        #split characters - split on common splitters
        for splitchar in [": ", " (", " %s"%channel.lower()]:
            if splitchar.lower() in title:
                title = title.split(splitchar)[0]
        #replace common chars and words
        re.sub('-|_', ' ',title)
        re.sub('\*|,|(|)|:|;|\"|`|_new|new_|.|\'|', '',title)
        return title
    
    def lookup_local_recordings(self, title):
        '''lookup actual recordings to get details for grouped recordings
           also grab a thumb provided by the pvr
        '''
        details = {}
        recordings = self.kodi_db.recordings()
        for item in recordings:
            if title.lower() in item["title"].lower():
                if item.get("art"):
                    details["thumbnail"] = get_clean_image(item["art"].get("thumb"))
                elif item.get("icon") and not "imagecache" in item["icon"]: #ignore tvheadend thumb as it returns the channellogo
                    details["thumbnail"] = get_clean_image(item["icon"])
        if len(recordings) > 1:
            details["media_type"] = "tvshow"
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
                details["media_type"] = "tvshow"
                for artkey, artvalue in details["art"].iteritems():
                    details["art"][artkey] = get_clean_image(artvalue)
        if not details and (not media_type or media_type == "movie"):
            kodi_items = self.kodi_db.movies(filters=filters,limits=(0,1))
            if kodi_items:
                details = kodi_items[0]
                details["media_type"] = "movie"
                for artkey, artvalue in details["art"].iteritems():
                    details["art"][artkey] = get_clean_image(artvalue)
        return details
        
    
 