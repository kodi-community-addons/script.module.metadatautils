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
import helpers.kodidb as kodidb
from helpers.pvrartwork import PvrArtwork
from helpers.studiologos import StudioLogos
from helpers.utils import log_msg, get_duration_string
from simplecache import SimpleCache, use_cache
import xbmc
    
class ArtUtils(object):
    '''
        Provides all kind of mediainfo for kodi media, returned as dict with details
        All functions have an optional tuple_list_prefix argument, if set, the output will be a list
        of tuples with strings directly usable as window property. The argument must be string which will be
        the prefix of the key in the list you want to set.
    '''
    studiologos_path = ""
    
    def __init__(self):
        self.kodidb = KodiDb()
        self.tmdb = Tmdb()
        self.fanarttv = FanartTv()
        self.google = GoogleImages()
        self.animatedart = AnimatedArt()
        self.omdb = Omdb()
        self.imdb = Imdb()
        self.pvrart = PvrArtwork()
        self.channellogos = ChannelLogos()
        self.studiologos = StudioLogos()
        self.cache = SimpleCache()
        
    def get_extrafanart(self,dbid, media_type, tuple_list_prefix=""):
        log_msg("get_extrafanart is not yet supported!")
        return ("empty","empty")
        
    @use_cache(14)
    def get_musicartwork(self, artist="",album="",title="",tuple_list_prefix=""):
        log_msg("get_musicartwork is not yet supported!")
        return ("empty","empty")
        
    @use_cache(14)
    def get_extended_artwork(self, imdb_id="",tvdb_id="",title="",year="",media_type="",tuple_list_prefix=""):
        '''returns details from tmdb'''
        log_msg("get_extended_artwork is not yet supported!")
        return [ ("empty","empty") ]
    
    @use_cache(14)
    def get_tmdb_details(self, imdb_id="",tvdb_id="",title="",year="",media_type="",tuple_list_prefix=""):
        '''returns details from tmdb'''
        if imdb_id and media_type in ["movies","setmovies", "movie"]:
            result = self.tmdb.get_movie_details_by_imdbid(imdb_id)
        elif tvdb_id and media_type in ["tvshows", "tvshow"]:
            result = self.tmdb.get_tvshow_details_by_tvdbid(tvdb_id)
        elif imdb_id and media_type in ["tvshows","tvshow"]:
            result = self.tmdb.get_tvshow_details_by_imdbid(imdb_id)
        elif title and media_type in ["movies","setmovies","movie"]:
            result = self.tmdb.search_movie(title, year)
        elif title and media_type in ["tvshows","tvshow"]:
            result = self.tmdb.search_tvshow(title, year)
        elif title:
            result = self.tmdb.search_video(title, year)
        else:
            result = {}
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
         
    def get_moviesetdetails(self,set_id,tuple_list_prefix=""):
        '''get a nicely formatted dict of the movieset details which we can for example set as window props'''
        details = {}
        if not set_id or set_id == "-1":
            log_msg("movieset-->  setid is none !!")
            return details
        #try to get from cache first - use checksum compare because moviesets do not get refreshed automatically
        movieset = self.kodidb.movieset(set_id,True)
        log_msg("movieset-->%s" %movieset)
        cache_checksum = [movie["playcount"] for movie in movieset["movies"]] if movieset else None
        cache_str = "MovieSetDetails.%s.%s"%(set_id,tuple_list_prefix)
        cache = self.cache.get(cache_str,checksum=cache_checksum)
        if cache:
            return details
        if movieset:
            count = 0
            runtime = 0
            unwatchedcount = 0
            watchedcount = 0
            runtime = 0
            writer = []
            director = []
            genre = []
            country = []
            studio = []
            years = []
            plot = ""
            title_list = ""
            total_movies = len(movieset['movies'])
            title_header = "[B]%s %s[/B][CR]"%(total_movies,xbmc.getLocalizedString(20342))
            all_fanarts = []
            for count, item in enumerate(movieset['movies']):
                if item["playcount"] == 0:
                    unwatchedcount += 1
                else:
                    watchedcount += 1
                
                #generic labels
                for label in ["label","plot","year","rating"]:
                    details['%s.%s'%(count,label)] = item[label]
                details["%s.DBID" %count] = item["movieid"]
                details["%s.Duration" %count] = item['runtime'] / 60
                
                #art labels
                art = item['art']
                for label in ["poster","fanart","landscape","clearlogo","clearart","banner","discart"]:
                    if art.get(label):
                        details['%s.%s'%(count,label)] = art[label]
                all_fanarts.append(art.get("fanart"))
                
                #streamdetails
                if item.get('streamdetails',''):
                    streamdetails = item["streamdetails"]
                    audiostreams = streamdetails.get('audio',[])
                    videostreams = streamdetails.get('video',[])
                    subtitles = streamdetails.get('subtitle',[])
                    if len(videostreams) > 0:
                        stream = videostreams[0]
                        height = stream.get("height","")
                        width = stream.get("width","")
                        if height and width:
                            resolution = ""
                            if width <= 720 and height <= 480: 
                                resolution = "480"
                            elif width <= 768 and height <= 576: 
                                resolution = "576"
                            elif width <= 960 and height <= 544: 
                                resolution = "540"
                            elif width <= 1280 and height <= 720: 
                                resolution = "720"
                            elif width <= 1920 and height <= 1080: 
                                resolution = "1080"
                            elif width * height >= 6000000: 
                                resolution = "4K"
                            details["%s.Resolution" %count] = resolution
                        details["%s.Codec" %count] = stream.get("codec","")
                        if stream.get("aspect",""):
                            details["%s.AspectRatio" %count] = round(stream["aspect"], 2)
                    if len(audiostreams) > 0:
                        #grab details of first audio stream
                        stream = audiostreams[0]
                        details["%s.AudioCodec" %count] = stream.get('codec','')
                        details["%s.AudioChannels" %count] = stream.get('channels','')
                        details["%s.AudioLanguage" %count] = stream.get('language','')
                    if len(subtitles) > 0:
                        #grab details of first subtitle
                        details["%s.SubTitle" %count] = subtitles[0].get('language','')

                title_list += "%s (%s)[CR]" %(item['label'],item['year'])
                if item['plotoutline']:
                    plot += "[B]%s (%s)[/B][CR]%s[CR][CR]" %(item['label'],item['year'],item['plotoutline'])
                else:
                    plot += "[B]%s (%s)[/B][CR]%s[CR][CR]" %(item['label'],item['year'],item['plot'])
                runtime += item['runtime']
                if item.get("writer"):
                    writer += [w for w in item["writer"] if w and w not in writer]
                if item.get("director"):
                    director += [d for d in item["director"] if d and d not in director]
                if item.get("genre"):
                    genre += [g for g in item["genre"] if g and g not in genre]
                if item.get("country"):
                    country += [c for c in item["country"] if c and c not in country]
                if item.get("studio"):
                    studio += [s for s in item["studio"] if s and s not in studio]
                years.append(str(item['year']))
            details["Plot"] = plot
            if total_movies > 1:
                details["ExtendedPlot"] = title_header + title_list + "[CR]" + plot
            else:
                details["ExtendedPlot"] = plot
            details["Title"] = title_list
            details["Runtime"] = runtime / 60
            duration = get_duration_string(runtime / 60)
            if duration:
                details["Duration"] = duration[2]
                details["Duration.Hours"] = duration[0]
                details["Duration.Minutes"] = duration[1]
                
            details["Writer"] = writer
            details["Director"] = director
            details["Genre"] = genre
            details["Studio"] = studio
            details["Years"] = years
            details["Extrafanarts"] = all_fanarts
            details.update( StudioLogos().get_studio_logo(studio, self.studiologos_path) )
            details["Count"] = total_movies
            details["extrafanartpath"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&path=movieset-%s"%set_id
            self.cache.set(cache_str,details,checksum=cache_checksum)
        if tuple_list_prefix:
            details = self.pretty_format_dict(result,tuple_list_prefix)
        return details
    
    @use_cache(14)
    def get_streamdetails(self,db_id,media_type,ignore_cache=False,tuple_list_prefix=""):
        '''get a nicely formatted dict of the streamdetails '''

        streamdetails = {}
        # get data from json
        if "movie" in media_type and not "movieset" in media_type:
            json_result = self.kodidb.movie(db_id)
        elif "episode" in media_type:
            json_result = self.kodidb.episode(db_id)
        elif "musicvideo" in media_type:
            json_result = self.kodidb.musicvideo(db_id)
        else:
            json_result = {}
            
        if json_result and json_result["streamdetails"]:
            audio = json_result["streamdetails"]['audio']
            subtitles = json_result["streamdetails"]['subtitle']
            video = json_result["streamdetails"]['video']
            all_audio_str = []
            all_subs = []
            all_lang = []
            for count, item in enumerate(audio):
                #audio codec
                codec = item['codec']
                if "ac3" in codec: 
                    codec = u"Dolby D"
                elif "dca" in codec: 
                    codec = u"DTS"
                elif "dts-hd" in codec or "dtshd" in codec: 
                    codec = u"DTS HD"
                #audio channels
                channels = item['channels']
                if channels == 1: 
                    channels = u"1.0"
                elif channels == 2: 
                    channels = u"2.0"
                elif channels == 3: 
                    channels = u"2.1"
                elif channels == 4: 
                    channels = u"4.0"
                elif channels == 5: 
                    channels = u"5.0"
                elif channels == 6: 
                    channels = u"5.1"
                elif channels == 7: 
                    channels = u"6.1"
                elif channels == 8: 
                    channels = u"7.1"
                elif channels == 9: 
                    channels = u"8.1"
                elif channels == 10: 
                    channels = u"9.1"
                else: 
                    channels = str(channels)
                #audio language
                language = item.get('language','')
                if language and language not in all_lang:
                    all_lang.append(language)
                streamdetails['AudioStreams.%d.Language'% count] = item['language']
                streamdetails['AudioStreams.%d.AudioCodec'%count] = item['codec']
                streamdetails['AudioStreams.%d.AudioChannels'%count] = str(item['channels'])
                audio_str = "-".join([language,codec,channels])
                streamdetails['AudioStreams.%d'%count] = audio_str
                all_audio_str.append(audio_str)
            subs_count = 0
            subs_count_unique = 0
            for item in subtitles:
                subs_count += 1
                if item['language'] not in all_subs:
                    all_subs.append(item['language'])
                    streamdetails['Subtitles.%d'%subs_count_unique] = item['language']
                    subs_count_unique += 1
            streamdetails['subtitles'] = all_subs
            streamdetails['subtitles.count'] = str(subs_count)
            streamdetails['allaudiostreams'] = all_audio_str
            streamdetails['audioStreams.count'] = str(len(all_audio_str))
            streamdetails['languages'] = all_lang
            streamdetails['languages.count'] = len(all_lang)
            if len(video) > 0:
                stream = video[0]
                streamdetails['videoheight'] = stream.get("height",0)
                streamdetails['videowidth'] = stream.get("width",0)
        if json_result.get("tag"):
            streamdetails["tags"] = json_result["tag"]
        if tuple_list_prefix:
            streamdetails = self.pretty_format_dict(streamdetails,tuple_list_prefix)
        return streamdetails
    
    def pretty_format_dict(self, details,prefix="SkinHelper.ListItem."):
        '''helper to pretty string-format a dict with details so it can be used as window props'''
        items = []
        for key, value in details.iteritems():
            if value:
                if prefix and not key.startswith(prefix.split(".")[0]):
                    key = "%s%s"%(prefix,key)
                if isinstance(value,(str,unicode)):
                    items.append( (key, value) )
                elif isinstance(value,(int,float)):
                    items.append( (key, "%s"%value) )
                elif isinstance(value,dict):
                    items.extend( self.pretty_format_dict(value, key + ".") )
                elif isinstance(value,list):
                    list_strings = []
                    for listvalue in value:
                        if isinstance(listvalue,(str,unicode)):
                            list_strings.append(listvalue)
                    if list_strings:
                        items.append( (key, " / ".join(list_strings) ) )
                    elif len(value) == 1 and isinstance(value[0], (str,unicode)):
                        items.append( (key, value ) )
                else:
                    log_msg("wrong value for key %s -  %s" %(key,value),xbmc.LOGWARNING)
        return items
        
    @use_cache(14)
    def get_pvr_artwork(title, channel="", year="", genre="", manual_lookup=False, ignore_cache=False, tuple_list_prefix=""):
        result = self.pvrart.get_pvr_artwork(title, channel, year, genre, manual_lookup, ignore_cache)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
    
    @use_cache(14)    
    def get_channellogo(self,channelname,tuple_list_prefix=""):
        result = self.channellogos.get_channellogo(channelname)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
        
    @use_cache(14)
    def get_studio_logo(self, studio,tuple_list_prefix=""):
        result = self.studiologos.get_studio_logo(studio, self.studiologos_path)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
        
    @use_cache(14)
    def get_animated_artwork(self, imdb_id, tuple_list_prefix=""):
        result = self.animatedart.get_animated_artwork(imdb_id)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
    
    @use_cache(14)
    def get_omdb_info(self, imdb_id, tuple_list_prefix=""):
        result = self.omdb.get_details_by_imdbid(imdb_id)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
        
    @use_cache(7)
    def get_top250_rating(self, imdb_id, tuple_list_prefix=""):
        result = self.imdb.get_top250_rating(imdb_id)
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result
        
    @use_cache(7)
    def get_duration(self, duration, tuple_list_prefix=""):
        log_msg("get duration called duration=%s - prefix=%s" %(duration,tuple_list_prefix))
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
        if tuple_list_prefix:
            return self.pretty_format_dict(result,tuple_list_prefix) if result else []
        return result

        
        
    
    
    