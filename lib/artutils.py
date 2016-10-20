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
from helpers.utils import log_msg, get_duration_string, log_exception
from simplecache import SimpleCache, use_cache
from thetvdb import TheTvDb
import xbmc
import datetime
    
class ArtUtils(object):
    '''
        Provides all kind of mediainfo for kodi media, returned as dict with details
    '''
    
    #path to use to lookup studio logos, must be set by the calling addon
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
        self.thetvdb = TheTvDb()
        self.cache = SimpleCache()
    
    #@use_cache(14)
    def get_extrafanart(self, dbid, media_type):
        result = {}
        log_msg("get_extrafanart is not yet supported!")
        return result
        
    #@use_cache(14)
    def get_musicartwork(self, artist="",album="",title=""):
        result = {}
        log_msg("get_musicartwork is not yet supported!")
        return result
        
    #@use_cache(14)
    def get_extended_artwork(self, imdb_id="",tvdb_id="",title="",year="",media_type=""):
        '''returns details from tmdb'''
        result = {}
        log_msg("get_extended_artwork is not yet supported!")
        return result
    
    @use_cache(14)
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
        details = {}
        #try to get from cache first
        #use checksum compare based on playcounts because moviesets do not get refreshed automatically
        movieset = self.kodidb.movieset(set_id,["playcount"])
        cache_str = "MovieSetDetails.%s"%(set_id)
        cache_checksum = []
        if movieset:
            cache_checksum = [movie["playcount"] for movie in movieset["movies"]]
            cache = self.cache.get(cache_str,checksum=cache_checksum)
            if cache:
                return cache
            #process movieset listing - get full movieset including all movie fields
            movieset = self.kodidb.movieset(set_id,kodi_constants.FIELDS_MOVIES)
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
            details["WatchedCount"] = watchedcount
            details["UnwatchedCount"] = unwatchedcount
            details["Extrafanarts"] = all_fanarts
            details.update( StudioLogos().get_studio_logo(studio, self.studiologos_path) )
            details["Count"] = total_movies
            details["extrafanartpath"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&fanarts=%s"%repr(all_fanarts)
        self.cache.set(cache_str,details,checksum=cache_checksum)
        return details
    
    @use_cache(14)
    def get_streamdetails(self,db_id,media_type,ignore_cache=False):
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
        return streamdetails
     
    def get_pvr_artwork(self, title, channel="", genre="", manual_select=False, ignore_cache=False):
        '''get artwork and mediadetails for PVR entries'''
        if not channel:
            #workaround for grouped recordings, lookup recordinginfo in local db'''
            recordings = self.kodidb.recordings()
            for item in recordings:
                if item["title"].lower() in title.lower() or title.lower() in item["label"].lower():
                    channel = item["channel"]
                    genre = " / ".join(item["genre"])
                    break
        return self.pvrart.get_pvr_artwork(title=title, channel=channel, genre=genre, manual_select=manual_select, ignore_cache=ignore_cache)
    
    @use_cache(14)    
    def get_channellogo(self,channelname):
        return self.channellogos.get_channellogo(channelname)
        
    @use_cache(14)
    def get_studio_logo(self, studio):
        return self.studiologos.get_studio_logo(studio, self.studiologos_path)
        
    @use_cache(14)
    def get_animated_artwork(self, imdb_id):
        return self.animatedart.get_animated_artwork(imdb_id)
    
    @use_cache(14)
    def get_omdb_info(self, imdb_id, title="", year="", content_type=""):
        title = title.split(" (")[0] #strip year appended to title
        if imdb_id:
            return self.omdb.get_details_by_imdbid(imdb_id)
        elif title and content_type in ["seasons","season","episodes","episode","tvshows","tvshow"]:
            return self.omdb.get_details_by_title(title,"","tvshows")
        elif title and year:
            return self.omdb.get_details_by_title(title,year,content_type)
        else:
            return {}
        
    @use_cache(7)
    def get_top250_rating(self, imdb_id):
        return self.imdb.get_top250_rating(imdb_id)
        
    @use_cache(7)
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

    @use_cache(7)
    def get_tvdb_details(self, imdbid="", tvdbid=""):
        result = {}
        showdetails = None
        self.thetvdb.days_ahead = 120
        if tvdbid:
            showdetails = self.thetvdb.get_series(tvdbid)
        elif imdbid:
            showdetails = self.thetvdb.get_series_by_imdb_id(imdbid)
        if showdetails:
            result = {
                        "status": showdetails["status"], #TODO: translate this
                        "tvdbid": showdetails["id"],
                        "tvdb.network": showdetails["network"],
                        "airsDayOfWeek": showdetails["airsDayOfWeek"],#TODO translate to regional format
                        "airsTime": showdetails["airsTime"],#TODO translate to regional format
                        "tvdb.rating": showdetails["siteRating"],
                        "tvdb.ratingcount": showdetails["siteRatingCount"],
                        "runtime": showdetails["runtime"] }
            if showdetails["status"] == "Continuing":
                #include next episode info
                eps_details = self.thetvdb.get_nextaired_episode(showdetails["id"])
                if eps_details:
                    result["nextepisode.title"] = eps_details["episodeName"]
                    result["nextepisode.airdate"] = datetime.datetime.strptime(eps_details["firstAired"],"%Y-%m-%d").date().strftime(xbmc.getRegion('datelong'))
                    result["nextepisode.episode"] = eps_details["airedEpisodeNumber"]
                    result["nextepisode.season"] = eps_details["airedSeason"]
                    result["nextepisode.thumb"] = eps_details.get("thumbnail","")
                    result["nextepisode.gueststars"] = eps_details["guestStars"]
                    result["nextepisode.director"] = eps_details["directors"]
                    result["nextepisode.writer"] = eps_details["writers"]
                    result["nextepisode.plot"] = eps_details["overview"]
            #include last episode info
            eps_details = self.thetvdb.get_last_episode_for_series(showdetails["id"])
            if eps_details:
                result["lastepisode.title"] = eps_details["episodeName"]
                result["lastepisode.airdate"] = datetime.datetime.strptime(eps_details["firstAired"],"%Y-%m-%d").date().strftime(xbmc.getRegion('datelong'))
                result["lastepisode.episode"] = eps_details["airedEpisodeNumber"]
                result["lastepisode.season"] = eps_details["airedSeason"]
                result["lastepisode.thumb"] = eps_details.get("thumbnail","")
                result["lastepisode.gueststars"] = eps_details["guestStars"]
                result["lastepisode.director"] = eps_details["directors"]
                result["lastepisode.writer"] = eps_details["writers"]
                result["lastepisode.plot"] = eps_details["overview"]
        return result
                    
 