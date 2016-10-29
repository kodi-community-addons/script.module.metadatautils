#!/usr/bin/python
# -*- coding: utf-8 -*-
from helpers.animatedart import AnimatedArt
from helpers.tmdb import Tmdb
from helpers.omdb import Omdb
from helpers.imdb import Imdb
from helpers.google import GoogleImages
from helpers.channellogos import ChannelLogos
from helpers.fanarttv import FanartTv
from helpers.kodidb import KodiDb
import helpers.kodi_constants as kodi_constants
from helpers.pvrartwork import PvrArtwork
from helpers.studiologos import StudioLogos
from helpers.musicartwork import MusicArtwork
from helpers.utils import log_msg, get_duration, log_exception, ADDON_ID, extend_dict, get_clean_image
from simplecache import use_cache, SimpleCache
from thetvdb import TheTvDb
import xbmc, xbmcaddon, xbmcvfs
import datetime
import os
    
class ArtUtils(object):
    '''
        Provides all kind of mediainfo for kodi media, returned as dict with details
    '''
    
    #path to use to lookup studio logos, must be set by the calling addon
    studiologos_path = ""
    
    def __init__(self):
        '''Initialize and load all our helpers'''
        self.cache = SimpleCache()
        self.addon = xbmcaddon.Addon(ADDON_ID)
        self.kodidb = KodiDb()
        self.omdb = Omdb(self.cache)
        self.tmdb = Tmdb(self.cache)
        self.channellogos = ChannelLogos(self.kodidb)
        self.fanarttv = FanartTv(self.cache)
        self.imdb = Imdb(self.cache)
        self.google = GoogleImages(self.cache)
        self.studiologos = StudioLogos(self.cache)
        self.animatedart = AnimatedArt(self.cache,self.kodidb)
        self.thetvdb = TheTvDb()
        self.musicart = MusicArtwork(self)
        self.pvrart = PvrArtwork(self)
        log_msg("Initialized")
        
    def close(self):
        '''Cleanup Kodi Cpython instances'''
        self.cache.close()
        del self.addon
        log_msg("Exited")
            
    @use_cache(14,True)
    def get_extrafanart(self, file_path, media_type):
        from helpers.extrafanart import get_extrafanart
        return get_extrafanart(file_path, media_type)
        
    def get_music_artwork(self, artist="",album="",title="", disc="", ignore_cache=False):
        result = {}
        return self.musicart.get_music_artwork(artist, album, track, disc,)
        
    def music_artwork_options(self, artist="",album="",title="", disc=""):
        '''options for music metadata for specific item'''
        return self.musicart.music_artwork_options(artist, album, title, disc)
        
    #@use_cache(14,True)
    def get_extended_artwork(self, imdb_id="",tvdb_id="",title="",year="",media_type=""):
        '''returns details from tmdb'''
        result = {}
        return result
    
    @use_cache(14,True)
    def get_tmdb_details(self, imdb_id="",tvdb_id="",title="",year="",media_type="", manual_select=False, preftype=""):
        '''returns details from tmdb'''
        result = {}
        title = title.split(" (")[0]
        if imdb_id:
            result = self.tmdb.get_video_details_by_external_id(imdb_id, "imdb_id")
        elif tvdb_id:
            result = self.tmdb.get_video_details_by_external_id(tvdb_id, "tvdb_id")
        elif title and media_type in ["movies","setmovies","movie"]:
            result = self.tmdb.search_movie(title, year, manual_select=manual_select)
        elif title and media_type in ["tvshows","tvshow"]:
            result = self.tmdb.search_tvshow(title, year, manual_select=manual_select)
        elif title:
            result = self.tmdb.search_video(title, year, preftype=preftype, manual_select=manual_select)
        if result.get("status"):
            result["status"] = self.translate_string(result["status"])
        if result.get("runtime"):
            result["runtime"] = result["runtime"] / 60
            result.update( get_duration(result["runtime"]) )
        return result
         
    def get_moviesetdetails(self,set_id):
        '''get a nicely formatted dict of the movieset details which we can for example set as window props'''
        from helpers.moviesetdetails import get_moviesetdetails
        return get_moviesetdetails(self.cache, self.kodidb, set_id, self.studiologos, self.studiologos_path)
    
    @use_cache(14,True)
    def get_streamdetails(self,db_id,media_type,ignore_cache=False):
        '''get a nicely formatted dict of the streamdetails '''
        from helpers.streamdetails import get_streamdetails
        return get_streamdetails(self.kodidb, db_id, media_type)
        
    def get_pvr_artwork(self, title, channel="", genre="", manual_select=False, ignore_cache=False):
        '''get artwork and mediadetails for PVR entries'''
        return self.pvrart.get_pvr_artwork(title, channel, genre, 
            manual_select=manual_select, ignore_cache=ignore_cache)
    
    def pvr_artwork_options(self, title, channel="", genre=""):
        '''options for pvr metadata for specific item'''
        return self.pvrart.pvr_artwork_options(title, channel, genre)
    
    @use_cache(14,True)    
    def get_channellogo(self,channelname):
        return self.channellogos.get_channellogo(channelname)
        
    def get_studio_logo(self, studio):
        #dont use cache at this level because of changing logospath
        return self.studiologos.get_studio_logo(studio, self.studiologos_path)
        
    @use_cache(14,False)
    def get_animated_artwork(self, imdb_id, ignore_cache=False, manual_select=False):
        return self.animatedart.get_animated_artwork(imdb_id, manual_select)
    
    @use_cache(14,True)
    def get_omdb_info(self, imdb_id, title="", year="", content_type=""):
        title = title.split(" (")[0] #strip year appended to title
        result = {}
        if imdb_id:
            result = self.omdb.get_details_by_imdbid(imdb_id)
        elif title and content_type in ["seasons","season","episodes","episode","tvshows","tvshow"]:
            result = self.omdb.get_details_by_title(title,"","tvshows")
        elif title and year:
            result = self.omdb.get_details_by_title(title, year, content_type)
        if result.get("status"):
            result["status"] = self.translate_string(result["status"])
        if result.get("runtime"):
            result["runtime"] = result["runtime"] / 60
            result.update( get_duration(result["runtime"]) )
        return result
        
    @use_cache(7,True)
    def get_top250_rating(self, imdb_id):
        return self.imdb.get_top250_rating(imdb_id)
        
    #@use_cache(7,True)
    def get_duration(self, duration):
        if ":" in duration:
            dur_lst = duration.split(":")
            return {
                    "Duration": "%s:%s" %(dur_lst[0],dur_lst[1]), 
                    "Duration.Hours": dur_lst[0], 
                    "Duration.Minutes": dur_lst[1],
                    "Runtime": str((int(dur_lst[0]) * 60) + dur_lst[1]),
                   }
        else:
            return get_duration(duration)

    @use_cache(1,True)
    def get_tvdb_details(self, imdbid="", tvdbid=""):
        result = {}
        self.thetvdb.days_ahead = 365
        if tvdbid:
            result = self.thetvdb.get_series(tvdbid)
        elif imdbid:
            result = self.thetvdb.get_series_by_imdb_id(imdbid)
        if result:
            if result["status"] == "Continuing":
                #include next episode info
                result["nextepisode"] = self.thetvdb.get_nextaired_episode(result["tvdb_id"])
            #include last episode info
            result["lastepisode"] = self.thetvdb.get_last_episode_for_series(result["tvdb_id"])
            result["status"] = self.translate_string(result["status"])
            if result.get("runtime"):
                result["runtime"] = result["runtime"] / 60
                result.update(get_duration(result["runtime"]))
        return result
                    
    def translate_string(self, _str):
        '''translate the received english string from the various sources like tvdb, tmbd etc'''
        translation = _str
        _str = _str.lower()
        if "continuing" in _str:
            translation = self.addon.getLocalizedString(32037)
        elif "ended" in _str:
            translation = self.addon.getLocalizedString(32038)
        elif "released" in _str:
            translation = self.addon.getLocalizedString(32040)
        return translation
     