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
from helpers.utils import log_msg, get_duration_string, log_exception, ADDON_ID
from simplecache import use_cache
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
    
    def __init__(self, simplecache=None):
        '''Initialize and load all our helpers - optionally provide simplecache instance'''
        if simplecache:
            self.cache = simplecache
        else:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        self.kodidb = KodiDb()
        self.omdb = Omdb(self.cache)
        self.tmdb = Tmdb(self.cache)
        self.pvrart = PvrArtwork(self)
        self.channellogos = ChannelLogos(self.kodidb)
        self.fanarttv = FanartTv(self.cache)
        self.imdb = Imdb(self.cache)
        self.google = GoogleImages(self.cache)
        self.studiologos = StudioLogos(self.cache)
        self.animatedart = AnimatedArt(self.cache,self.kodidb)
        self.thetvdb = TheTvDb(self.cache)
        self.addon = xbmcaddon.Addon(ADDON_ID)
        log_msg("Initialized")
        
    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.addon
        log_msg("MainModule exited")
    
    @use_cache(14,True)
    def get_extrafanart(self, file_path, media_type):
        from helpers.extrafanart import get_extrafanart
        return get_extrafanart(file_path, media_type)
        
    def get_musicartwork(self, artist="",album="",title=""):
        result = {}
        return result
        
    #@use_cache(14,True)
    def get_extended_artwork(self, imdb_id="",tvdb_id="",title="",year="",media_type=""):
        '''returns details from tmdb'''
        result = {}
        return result
    
    @use_cache(14,True)
    def get_tmdb_details(self, imdb_id="",tvdb_id="",title="",year="",media_type=""):
        '''returns details from tmdb'''
        result = {}
        title = title.split(" (")[0]
        if imdb_id:
            result = self.tmdb.get_video_details_by_external_id(imdb_id, "imdb_id")
        elif tvdb_id:
            result = self.tmdb.get_video_details_by_external_id(tvdb_id, "tvdb_id")
        elif title and media_type in ["movies","setmovies","movie"]:
            result = self.tmdb.search_movie(title, year)
        elif title and media_type in ["tvshows","tvshow"]:
            result = self.tmdb.search_tvshow(title, year)
        elif title:
            result = self.tmdb.search_video(title, year)
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
        if imdb_id:
            return self.omdb.get_details_by_imdbid(imdb_id)
        elif title and content_type in ["seasons","season","episodes","episode","tvshows","tvshow"]:
            return self.omdb.get_details_by_title(title,"","tvshows")
        elif title and year:
            return self.omdb.get_details_by_title(title, year, content_type)
        else:
            return {}
        
    @use_cache(7,True)
    def get_top250_rating(self, imdb_id):
        return self.imdb.get_top250_rating(imdb_id)
        
    @use_cache(7,True)
    def get_duration(self, duration):
        result = {}
        if ":" in duration:
            dur_lst = duration.split(":")
            if len(dur_lst) == 1:
                duration = "0"
            elif len(dur_lst) == 2:
                duration = dur_lst[0]
            elif len(dur_lst) == 3:
                duration = str((int(dur_lst[0])*60) + int(dur_lst[1]))
        if duration:
            duration_str = get_duration_string(duration)
            if duration_str:
                result['Duration'] =  duration_str[2]
                result['Duration.Hours'] =  duration_str[0]
                result['Duration.Minutes'] =  duration_str[1]
        return result

    @use_cache(7,True)
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
                eps_details = self.thetvdb.get_nextaired_episode(result["tvdb_id"])
                if eps_details:
                    result["nextepisode.title"] = eps_details["episodeName"]
                    result["nextepisode.airdate"] = datetime.datetime.strptime(eps_details["firstAired"],
                        "%Y-%m-%d").date().strftime(xbmc.getRegion('dateshort'))
                    result["nextepisode.airdate.long"] = datetime.datetime.strptime(eps_details["firstAired"],
                        "%Y-%m-%d").date().strftime(xbmc.getRegion('datelong'))
                    result["nextepisode.episode"] = eps_details["airedEpisodeNumber"]
                    result["nextepisode.season"] = eps_details["airedSeason"]
                    result["nextepisode.thumb"] = eps_details.get("thumbnail","")
                    result["nextepisode.gueststars"] = eps_details["guestStars"]
                    result["nextepisode.director"] = eps_details["directors"]
                    result["nextepisode.writer"] = eps_details["writers"]
                    result["nextepisode.plot"] = eps_details["overview"]
                    eps_lbl = str(eps_details["airedEpisodeNumber"]).zfill(2)
                    seas_lbl = str(eps_details["airedSeason"]).zfill(2)
                    result["nextepisode.label"] = "S%sE%s %s (%s)" %(seas_lbl, eps_lbl, eps_details["episodeName"], 
                        result["nextepisode.airdate"])
            #include last episode info
            eps_details = self.thetvdb.get_last_episode_for_series(result["tvdb_id"])
            if eps_details:
                result["lastepisode.title"] = eps_details["episodeName"]
                result["lastepisode.airdate"] = datetime.datetime.strptime(eps_details["firstAired"],
                    "%Y-%m-%d").date().strftime(xbmc.getRegion('dateshort'))
                result["lastepisode.airdate.long"] = datetime.datetime.strptime(eps_details["firstAired"],
                    "%Y-%m-%d").date().strftime(xbmc.getRegion('datelong'))
                result["lastepisode.episode"] = eps_details["airedEpisodeNumber"]
                result["lastepisode.season"] = eps_details["airedSeason"]
                result["lastepisode.thumb"] = eps_details.get("thumbnail","")
                result["lastepisode.gueststars"] = eps_details["guestStars"]
                result["lastepisode.director"] = eps_details["directors"]
                result["lastepisode.writer"] = eps_details["writers"]
                result["lastepisode.plot"] = eps_details["overview"]
                eps_lbl = str(eps_details["airedEpisodeNumber"]).zfill(2)
                seas_lbl = str(eps_details["airedSeason"]).zfill(2)
                result["lastepisode.label"] = "S%sE%s %s (%s)" %(seas_lbl, eps_lbl, eps_details["episodeName"], 
                    result["lastepisode.airdate"])
        return result
                    
 