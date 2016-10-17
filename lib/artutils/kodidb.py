#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcgui
from utils import json, try_encode, log_msg, log_exception, get_clean_image, get_duration_string, ADDON
import studiologos
import simplecache

FIELDS_BASE = ["dateadded", "file", "lastplayed","plot", "title", "art", "playcount"]
FIELDS_FILE = FIELDS_BASE + ["streamdetails", "director", "resume", "runtime"]
FIELDS_MOVIES = FIELDS_FILE + ["plotoutline", "sorttitle", "cast", "votes", "showlink", "top250", "trailer", "year",
    "country", "studio", "set", "genre", "mpaa", "setid", "rating", "tag", "tagline", "writer", "originaltitle",
    "imdbnumber"]
FIELDS_TVSHOWS = FIELDS_BASE + ["sorttitle", "mpaa", "premiered", "year", "episode", "watchedepisodes", "votes",
    "rating", "studio", "season", "genre", "cast", "episodeguide", "tag", "originaltitle", "imdbnumber"]
FIELDS_EPISODES = FIELDS_FILE + ["cast", "productioncode", "rating", "votes", "episode", "showtitle", "tvshowid",
    "season", "firstaired", "writer", "originaltitle"]
FIELDS_MUSICVIDEOS = FIELDS_FILE + ["genre", "artist", "tag", "album", "track", "studio", "year"]
FIELDS_FILES = FIELDS_FILE + ["plotoutline", "sorttitle", "cast", "votes", "trailer", "year", "country", "studio",
    "genre", "mpaa", "rating", "tagline", "writer", "originaltitle", "imdbnumber", "premiered","episode", "showtitle",
    "firstaired","watchedepisodes","duration"]
FIELDS_SONGS = ["artist","displayartist", "title", "rating", "fanart", "thumbnail", "duration",
    "playcount", "comment", "file", "album", "lastplayed", "genre", "musicbrainzartistid", "track"]
FIELDS_ALBUMS = ["title", "fanart", "thumbnail", "genre", "displayartist", "artist", "genreid",
    "musicbrainzalbumartistid", "year", "rating", "artistid", "musicbrainzalbumid", "theme", "description",
    "type", "style", "playcount", "albumlabel", "mood"]
FIELDS_PVR = ["art", "channel", "directory", "endtime", "file", "genre", "icon", "playcount", "plot",
    "plotoutline", "resume", "runtime", "starttime", "streamurl", "title"]

FILTER_UNWATCHED = {"operator":"lessthan", "field":"playcount", "value":"1"}
FILTER_WATCHED = {"operator":"isnot", "field":"playcount", "value":"0"}
FILTER_RATING = {"operator":"greaterthan","field":"rating", "value":"7"}
FILTER_INPROGRESS = {"operator":"true", "field":"inprogress", "value":""}
SORT_RATING = {"method": "rating", "order": "descending"}
SORT_RANDOM = {"method": "random", "order": "descending"}
SORT_TITLE = {"method": "title", "order": "ascending"}
SORT_DATEADDED = {"method": "dateadded", "order": "descending"}
SORT_LASTPLAYED = {"method": "lastplayed", "order": "descending"}
SORT_EPISODE = {"method": "episode"}

class KodiDb(object):
    '''various methods and helpers to get data from kodi json api'''
    
    def movie(self,db_id):
        '''get moviedetails from kodi db'''
        return self.get_json("VideoLibrary.GetMovieDetails",returntype="moviedetails",
            fields=FIELDS_MOVIES,optparam=("movieid",int(db_id)))
    
    def movies(self,sort=None, filters=None, limits=None, filtertype=None):
        '''get moviedetails from kodi db'''
        return self.get_json("VideoLibrary.GetMovies", sort=sort, filters=filters, 
            fields=FIELDS_MOVIES, limits=limits, returntype="movies", filtertype=filtertype)
            
    def movie_by_imdbid(self,imdb_id):
        '''gets a movie from kodidb by imdbid.'''
        filters = [{ "operator":"is", "field":"imdbnumber", "value":imdb_id}]
        movies = self.movies(self,filters=filters)
        return movies[0] if movies else None
    
    def tvshow(self,db_id):
        '''get tvshow from kodi db'''
        return self.get_json("VideoLibrary.GetTvShowDetails",returntype="tvshowdetails",
            fields=FIELDS_TVSHOWS,optparam=("tvshowid",int(db_id)))
    
    def tvshows(self,sort=None, filters=None, limits=None, filtertype=None):
        '''get tvshows from kodi db'''
        return self.get_json("VideoLibrary.GetTvShows", sort=sort, filters=filters, 
            fields=FIELDS_TVSHOWS, limits=limits, returntype="tvshows", filtertype=filtertype)
            
    def tvshow_by_imdbid(self,imdb_id):
        '''gets a tvshow from kodidb by imdbid.'''
        filters = [{ "operator":"is", "field":"imdbnumber", "value":imdb_id}]
        tvshows = self.tvshows(self,filters=filters)
        return tvshows[0] if tvshows else None
    
    def episode(self,db_id):
        '''get episode from kodi db'''
        return self.get_json("VideoLibrary.GetEpisodeDetails",returntype="episodedetails",
            fields=FIELDS_EPISODES,optparam=("episodeid",int(db_id)))
    
    def episodes(self,sort=None, filters=None, limits=None, filtertype=None, tvshowid=None):
        '''get episodes from kodi db'''
        if tvshowid:
            params = ( "tvshowid", int(tvshowid) )
        else:
            params=None
        return self.get_json("VideoLibrary.GetEpisodes", sort=sort, filters=filters, 
            fields=FIELDS_EPISODES, limits=limits, returntype="episodes", filtertype=filtertype, optparam=params)
            
    def musicvideo(self,db_id):
        '''get musicvideo from kodi db'''
        return self.get_json("VideoLibrary.GetMusicVideoDetails",returntype="musicvideodetails",
            fields=FIELDS_MUSICVIDEOS,optparam=("musicvideoid",int(db_id)))
    
    def musicvideos(self,sort=None, filters=None, limits=None, filtertype=None):
        '''get musicvideos from kodi db'''
        return self.get_json("VideoLibrary.GetMusicVideos", sort=sort, filters=filters, 
            fields=FIELDS_MUSICVIDEOS, limits=limits, returntype="musicvideos", filtertype=filtertype)
           
    def recording(self,db_id):
        '''get pvr recording from kodi db'''
        return self.get_json("PVR.GetRecordingDetails",returntype="recordingdetails",
            fields=FIELDS_PVR,optparam=("recordingid",int(db_id)))
    
    def recordings(self,sort=None, filters=None, limits=None, filtertype=None):
        '''get pvr recordings from kodi db'''
        return self.get_json("PVR.GetRecordings", sort=sort, filters=filters, 
            fields=FIELDS_PVR, limits=limits, returntype="recordings", filtertype=filtertype)
    
    def movieset(self,db_id,include_set_movies=False):
        '''get movieset from kodi db'''
        if include_set_movies:
            optparams = [("moviesetid",int(db_id)), ("movies", {"properties": FIELDS_MOVIES})]
        else:
            optparams = ("moviesetid",int(db_id))
        return self.get_json("VideoLibrary.GetMovieSetDetails",returntype="moviesetdetails",
            fields=FIELDS_BASE,optparam=optparams)
    
    def moviesets(self,sort=None, filters=None, limits=None, filtertype=None,include_set_movies=False):
        '''get moviesetdetails from kodi db'''
        if include_set_movies:
            optparams = ( "movies", {"properties": FIELDS_MOVIES} )
        else:
            optparams = None
        return self.get_json("VideoLibrary.GetMovieSets", sort=sort, filters=filters, 
            fields=FIELDS_BASE, limits=limits, returntype="moviesets", filtertype=filtertype)
    
    def moviesetdetails(self,set_id):
        '''get a nicely formatted dict of the movieset details which we can for example set as window props'''
        if not set_id:
            return
        #try to get from cache first - use checksum compare because moviesets do not get refreshed automatically
        movieset = self.movieset(set_id,True)
        cache_checksum = [movie["playcount"] for movie in movieset["movies"]] if movieset else None
        cache_str = "MovieSetDetails.%s"%set_id
        cache = simplecache.get(cache_str,checksum=cache_checksum)
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
            title_header = "[B]" + total_movies + " " + xbmc.getLocalizedString(20342) + "[/B][CR]"
            all_fanarts = []
            for count, item in movieset['movies'].enumerate():
                if item["playcount"] == 0:
                    unwatchedcount += 1
                else:
                    watchedcount += 1
                
                #generic labels
                for label in ["label","plot","year","rating"]:
                    details['%.%s'%(count,label)] = item[label]
                details["%s.DBID" %count] = item["movieid"]
                details["%s.Duration" %count] = item['runtime'] / 60
                
                #art labels
                art = item['art']
                for label in ["poster","fanart","landscape","clearlogo","clearart","banner","discart"]:
                    if art.get(label):
                        details['%.%s'%(count,label)] = item[label]
                all_fanarts.append(item.get("fanart"))
                
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
            if durationString:
                details["Duration"] = duration[2]
                details["Duration.Hours"] = duration[0]
                details["Duration.Minutes"] = duration[1]
                
            details["Writer"] = " / ".join(writer)
            details["Director"] = " / ".join(director)
            details["Genre"] = " / ".join(genre)
            details["Studio"] = " / ".join(studio)
            details["Years"] = " / ".join(years)
            details["Extrafanarts"] = set_fanart
            details += StudioLogos().get_studio_logo(studio)
            details["Count"] = total_movies
            details["extrafanartpath"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&path=movieset-%s"%set_id
        #save to cache and return
        simplecache.set(cache_str,details,checksum=cache_checksum)
        return details
    
    def streamdetails(self,db_id,media_type,ignore_cache=False):
        '''get a nicely formatted dict of the streamdetails which we can for example set as window props'''
        
        #we need valid input
        if not db_id or not media_type or int(db_id) == -1:
            return {}
            
        #get the item from cache first
        cache_str = u"SkinHelper.StreamDetails.%s.%s" %(db_id,media_type)
        cache = simplecache.get(cache_str)
        if cache and not ignore_cache:
            return cache

        # no cache - get data from json
        json_result = {}
        streamdetails = {}
        # get data from json
        if "movie" in media_type:
            json_result = self.movie(db_id)
        elif "episode" in media_type:
            json_result = self.episode(db_id)
        elif "musicvideo" in media_type:
            json_result = self.musicvideo(db_id)
            
        if json_result and json_result["streamdetails"]:
            audio = json_result["streamdetails"]['audio']
            subtitles = json_result["streamdetails"]['subtitle']
            video = json_result["streamdetails"]['video']
            all_audio_str = []
            all_subs = []
            all_lang = []
            for count, item in audio.enumerate():
                #audio codec
                codec = item['codec']
                if "ac3" in codec: 
                    codec = "Dolby D"
                elif "dca" in codec: 
                    codec = "DTS"
                elif "dts-hd" in codec or "dtshd" in codec: 
                    codec = "DTS HD"
                #audio channels
                channels = item['channels']
                if channels == 1: 
                    channels = "1.0"
                elif channels == 2: 
                    channels = "2.0"
                elif channels == 3: 
                    channels = "2.1"
                elif channels == 4: 
                    channels = "4.0"
                elif channels == 5: 
                    channels = "5.0"
                elif channels == 6: 
                    channels = "5.1"
                elif channels == 7: 
                    channels = "6.1"
                elif channels == 8: 
                    channels = "7.1"
                elif channels == 9: 
                    channels = "8.1"
                elif channels == 10: 
                    channels = "9.1"
                else: 
                    channels = str(channels)
                #audio language
                language = item.get('language','')
                if language and language not in all_lang:
                    all_lang.append(language)
                streamdetails['AudioStreams.%d.Language'% count] = item['language']
                streamdetails['AudioStreams.%d.AudioCodec'%count] = item['codec']
                streamdetails['AudioStreams.%d.AudioChannels'%count] = str(item['channels'])
                audio_str = u"•".join([language,codec,channels])
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
            streamdetails['subtitles'] = u" / ".join(all_subs)
            streamdetails['subtitles.count'] = str(subs_count)
            streamdetails['allaudiostreams'] = u" / ".join(all_audio_str)
            streamdetails['audioStreams.count'] = str(len(all_audio_str))
            streamdetails['languages'] = u" / ".join(all_lang)
            streamdetails['languages.count'] = str(len(all_lang))
            if len(video) > 0:
                stream = video[0]
                streamdetails['videoheight'] = str(stream.get("height",""))
                streamdetails['videowidth'] = str(stream.get("width",""))
        if json_result.get("tag"):
            streamdetails["tags"] = u" / ".join(json_result["tag"])
        simplecache.set(cache_str,streamdetails)
        return streamdetails
 
    def files(self, vfspath):
        '''gets all items in a kodi vfs path'''
        params = {}
        params["directory"] = vfspath
        return self.get_json("Files.GetDirectory",returntype="",opt_params=params,fields=FIELDS_FILES)
    
    def genres(self, media_type):
        '''return all genres for the given media type (movie/tvshow/musicvideo)'''
        return self.get_json("VideoLibrary.GetGenres", fields=["thumbnail","title"], returntype="genres", optparam=("type",media_type))
    
    @staticmethod    
    def set_json(method,params):
        kodi_json = {}
        kodi_json["jsonrpc"] = "2.0"
        kodi_json["method"] = jsonmethod
        kodi_json["params"] = params
        kodi_json["id"] = 1
        json_response = xbmc.executeJSONRPC(try_encode(json.dumps(kodi_json)))
        return json.loads(json_response.decode('utf-8','replace'))

    @staticmethod
    def get_json(jsonmethod,sort=None,filters=None,fields=None,limits=None,returntype=None,optparam=None,filtertype=None):
        kodi_json = {}
        kodi_json["jsonrpc"] = "2.0"
        kodi_json["method"] = jsonmethod
        kodi_json["params"] = {}
        if optparam:
            if isinstance(optparam,list):   
                for param in optparam:
                    kodi_json["params"][param[0]] = param[1]
            else:
                kodi_json["params"][optparam[0]] = optparam[1]
        kodi_json["id"] = 1
        if sort:
            kodi_json["params"]["sort"] = sort
        if filters:
            if not filtertype:
                filtertype = "and"
            if len(filters) > 1:
                kodi_json["params"]["filter"] = {}
                kodi_json["params"]["filter"][filtertype] = filters
            else:
                kodi_json["params"]["filter"] = filters[0]
        if fields:
            kodi_json["params"]["properties"] = fields
        if limits:
            kodi_json["params"]["limits"] = { "start": limits[0], "end": limits[1] }
        json_response = xbmc.executeJSONRPC(try_encode(json.dumps(kodi_json)))
        json_object = json.loads(json_response.decode('utf-8','replace'))
        result = {}
        if 'result' in json_object:
            if returntype and returntype in json_object['result']:
                #returntype specified, return immediately
                result = json_object['result'][returntype]
            else:
                #no returntype specified, we'll have to look for it
                for key, value in json_object['result'].iteritems():
                    if not key=="limits" and (isinstance(value, list) or isinstance(value,dict)):
                        result = value
        return result

    @staticmethod
    def create_listitem(item,as_tuple=True):
        '''helper to create a kodi listitem from kodi compatible dict with mediainfo'''
        try:
            liz = xbmcgui.ListItem(label=item.get("label",""),label2=item.get("label2",""))
            liz.setProperty('IsPlayable', item.get('IsPlayable','true'))
            liz.setPath(item.get('file'))

            nodetype = "Video"
            if item["type"] in ["song","album","artist"]:
                nodetype = "Music"

            #extra properties
            for key, value in item["extraproperties"].iteritems():
                liz.setProperty(key, value)

            #video infolabels
            if nodetype == "Video":
                infolabels = {
                    "title": item.get("title"),
                    "size": item.get("size"),
                    "genre": item.get("genre"),
                    "year": item.get("year"),
                    "top250": item.get("top250"),
                    "tracknumber": item.get("tracknumber"),
                    "rating": item.get("rating"),
                    "playcount": item.get("playcount"),
                    "overlay": item.get("overlay"),
                    "cast": item.get("cast"),
                    "castandrole": item.get("castandrole"),
                    "director": item.get("director"),
                    "mpaa": item.get("mpaa"),
                    "plot": item.get("plot"),
                    "plotoutline": item.get("plotoutline"),
                    "originaltitle": item.get("originaltitle"),
                    "sorttitle": item.get("sorttitle"),
                    "duration": item.get("duration"),
                    "studio": item.get("studio"),
                    "tagline": item.get("tagline"),
                    "writer": item.get("writer"),
                    "tvshowtitle": item.get("tvshowtitle"),
                    "premiered": item.get("premiered"),
                    "status": item.get("status"),
                    "code": item.get("imdbnumber"),
                    "aired": item.get("aired"),
                    "credits": item.get("credits"),
                    "album": item.get("album"),
                    "artist": item.get("artist"),
                    "votes": item.get("votes"),
                    "trailer": item.get("trailer"),
                    "progress": item.get('progresspercentage')
                }
                if "DBID" in item["extraproperties"] and item["type"] not in ["tvrecording","tvchannel","favourite"]:
                    infolabels["mediatype"] = item["type"]
                    infolabels["dbid"] = item["extraproperties"]["DBID"]
                if "date" in item: infolabels["date"] = item["date"]
                if "lastplayed" in item: infolabels["lastplayed"] = item["lastplayed"]
                if "dateadded" in item: infolabels["dateadded"] = item["dateadded"]
                if item["type"] == "episode":
                    infolabels["season"] = item["season"]
                    infolabels["episode"] = item["episode"]

                liz.setInfo( type="Video", infoLabels=infolabels)

                #streamdetails
                if item.get("streamdetails"):
                    liz.addStreamInfo("video", item["streamdetails"].get("video",{}))
                    liz.addStreamInfo("audio", item["streamdetails"].get("audio",{}))
                    liz.addStreamInfo("subtitle", item["streamdetails"].get("subtitle",{}))

            #music infolabels
            if nodetype == "Music":
                infolabels = {
                    "title": item.get("title"),
                    "size": item.get("size"),
                    "genre": item.get("genre"),
                    "year": item.get("year"),
                    "tracknumber": item.get("track"),
                    "album": item.get("album"),
                    "artist": " / ".join(item.get('artist')),
                    "rating": str(item.get("rating",0)),
                    "lyrics": item.get("lyrics"),
                    "playcount": item.get("playcount")
                }
                if "date" in item: infolabels["date"] = item["date"]
                if "duration" in item: infolabels["duration"] = item["duration"]
                if "lastplayed" in item: infolabels["lastplayed"] = item["lastplayed"]
                liz.setInfo( type="Music", infoLabels=infolabels)

            #artwork
            liz.setArt( item.get("art", {}))
            if "icon" in item:
                liz.setIconImage(item['icon'])
            if "thumbnail" in item:
                liz.setThumbnailImage(item['thumbnail'])
                
            #contextmenu
            if item["type"] in ["episode","season"] and "season" in item and "tvshowid" in item:
                #add series and season level to widgets
                if not "contextmenu" in item:
                    item["contextmenu"] = []
                item["contextmenu"] += [ 
                    (ADDON.getLocalizedString(32051), "ActivateWindow(Video,videodb://tvshows/titles/%s/,return)"
                        %(item["tvshowid"])),
                    (ADDON.getLocalizedString(32052), "ActivateWindow(Video,videodb://tvshows/titles/%s/%s/,return)"
                        %(item["tvshowid"],item["season"])) ]
            if "contextmenu" in item:
                liz.addContextMenuItems(item["contextmenu"])
        
            if as_tuple:
                return (item["file"], liz, item.get("isFolder",False))
            else:
                return liz
        except Exception as exc:
            log_exception(__name__,exc)
            return None
    
    @staticmethod
    def prepare_listitem(item):
        '''helper to convert kodi output from json api to compatible format for listitems'''
        try:
            #fix values returned from json to be used as listitem values
            properties = item.get("extraproperties",{})

            #set type
            for idvar in [ ('episode','DefaultTVShows.png'),('tvshow','DefaultTVShows.png'),('movie','DefaultMovies.png'),('song','DefaultAudio.png'),('musicvideo','DefaultMusicVideos.png'),('recording','DefaultTVShows.png'),('album','DefaultAudio.png') ]:
                if item.get(idvar[0] + "id"):
                    properties["DBID"] = str(item.get(idvar[0] + "id"))
                    if not item.get("type"): item["type"] = idvar[0]
                    if not item.get("icon"): item["icon"] = idvar[1]
                    break

            #general properties
            if item.get('genre') and isinstance(item.get('genre'), list): item["genre"] = " / ".join(item.get('genre'))
            if item.get('studio') and isinstance(item.get('studio'), list): item["studio"] = " / ".join(item.get('studio'))
            if item.get('writer') and isinstance(item.get('writer'), list): item["writer"] = " / ".join(item.get('writer'))
            if item.get('director') and isinstance(item.get('director'), list): item["director"] = " / ".join(item.get('director'))
            if not isinstance(item.get('artist'), list) and item.get('artist'): item["artist"] = [item.get('artist')]
            if not item.get('artist'): item["artist"] = []
            if item.get('type') == "album" and not item.get('album'): item['album'] = item.get('label')
            if not item.get("duration") and item.get("runtime"): item["duration"] = item.get("runtime")
            if not item.get("plot") and item.get("comment"): item["plot"] = item.get("comment")
            if not item.get("tvshowtitle") and item.get("showtitle"): item["tvshowtitle"] = item.get("showtitle")
            if not item.get("premiered") and item.get("firstaired"): item["premiered"] = item.get("firstaired")
            if not properties.get("imdbnumber") and item.get("imdbnumber"): properties["imdbnumber"] = item.get("imdbnumber")
            properties["dbtype"] = item.get("type")
            properties["type"] = item.get("type")
            properties["path"] = item.get("file")

            #cast
            listCast = []
            listCastAndRole = []
            if item.get("cast") and isinstance(item["cast"],list):
                for castmember in item["cast"]:
                    if isinstance(castmember,dict):
                        listCast.append( castmember.get("name","") )
                        listCastAndRole.append( (castmember["name"], castmember["role"]) )
                    else:
                        listCast.append( castmember )
                        listCastAndRole.append( (castmember, "") )

            item["cast"] = listCast
            item["castandrole"] = listCastAndRole

            if item.get("season") and item.get("episode"):
                properties["episodeno"] = "s%se%s" %(item.get("season"),item.get("episode"))
            if item.get("resume"):
                properties["resumetime"] = str(item['resume']['position'])
                properties["totaltime"] = str(item['resume']['total'])
                properties['StartOffset'] = str(item['resume']['position'])

            #streamdetails
            if item.get("streamdetails"):
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
                        if width <= 720 and height <= 480: resolution = "480"
                        elif width <= 768 and height <= 576: resolution = "576"
                        elif width <= 960 and height <= 544: resolution = "540"
                        elif width <= 1280 and height <= 720: resolution = "720"
                        elif width <= 1920 and height <= 1080: resolution = "1080"
                        elif width * height >= 6000000: resolution = "4K"
                        properties["VideoResolution"] = resolution
                    if stream.get("codec",""):
                        properties["VideoCodec"] = str(stream["codec"])
                    if stream.get("aspect",""):
                        properties["VideoAspect"] = str(round(stream["aspect"], 2))
                    item["streamdetails"]["video"] = stream

                #grab details of first audio stream
                if len(audiostreams) > 0:
                    stream = audiostreams[0]
                    properties["AudioCodec"] = stream.get('codec','')
                    properties["AudioChannels"] = str(stream.get('channels',''))
                    properties["AudioLanguage"] = stream.get('language','')
                    item["streamdetails"]["audio"] = stream

                #grab details of first subtitle
                if len(subtitles) > 0:
                    properties["SubtitleLanguage"] = subtitles[0].get('language','')
                    item["streamdetails"]["subtitle"] = subtitles[0]
            else:
                item["streamdetails"] = {}
                item["streamdetails"]["video"] =  {'duration': item.get('duration',0)}

            #additional music properties
            if item.get('album_description'):
                properties["Album_Description"] = item.get('album_description')

            #pvr properties
            if item.get("starttime"):
                starttime = get_localdate_from_utc(item['starttime'])
                endtime = get_localdate_from_utc(item['endtime'])
                properties["StartTime"] = starttime[1]
                properties["StartDate"] = starttime[0]
                properties["EndTime"] = endtime[1]
                properties["EndDate"] = endtime[0]
                fulldate = starttime[0] + " " + starttime[1] + "-" + endtime[1]
                properties["Date"] = fulldate
                properties["StartDateTime"] = starttime[0] + " " + starttime[1]
                item["date"] = starttime[0]
                item["premiered"] = starttime[0]
            if item.get("channellogo"):
                properties["channellogo"] = item["channellogo"]
                properties["channelicon"] = item["channellogo"]
            if item.get("episodename"): properties["episodename"] = item.get("episodename","")
            if item.get("channel"): properties["channel"] = item.get("channel","")
            if item.get("channel"): properties["channelname"] = item.get("channel","")
            if item.get("channel"): item["label2"] = item.get("channel","")

            #artwork
            art = item.get("art",{})
            if item["type"] in ["episode","season"]:
                if not art.get("fanart") and art.get("season.fanart"):
                    art["fanart"] = art["season.fanart"]
                if not art.get("poster") and art.get("season.poster"):
                    art["poster"] = art["season.poster"]
                if not art.get("landscape") and art.get("season.landscape"):
                    art["poster"] = art["season.landscape"]
                if not art.get("fanart") and art.get("tvshow.fanart"):
                    art["fanart"] = art.get("tvshow.fanart")
                if not art.get("poster") and art.get("tvshow.poster"):
                    art["poster"] = art.get("tvshow.poster")
                if not art.get("clearlogo") and art.get("tvshow.clearlogo"):
                    art["clearlogo"] = art.get("tvshow.clearlogo")
                if not art.get("landscape") and art.get("tvshow.landscape"):
                    art["landscape"] = art.get("tvshow.landscape")
            if not art.get("fanart") and item.get('fanart'): art["fanart"] = item.get('fanart')
            if not art.get("thumb") and item.get('thumbnail'): art["thumb"] = get_clean_image(item.get('thumbnail'))
            if not art.get("thumb") and art.get('poster'): art["thumb"] = get_clean_image(item.get('poster'))
            if not art.get("thumb") and item.get('icon'): art["thumb"] = get_clean_image(item.get('icon'))
            if not item.get("thumbnail") and art.get('thumb'): item["thumbnail"] = art["thumb"]

            item["extraproperties"] = properties
            
            if not "file" in item:
                log_msg("Item is missing file path ! --> %s" %item["label"], xbmc.LOGWARNING)
                item["file"] = ""
            
            #return the result
            return item

        except Exception as exc:
            log_exception(__name__,exc)
            return None

    @staticmethod
    def create_main_entry(item):
        '''helper to create a simple (directory) listitem'''
        return {
                "label": item[0], 
                "file": "plugin://script.skin.helper.widgets/?action=%s" %item[1],
                "icon": item[2],
                "art": {"fanart": "special://home/addons/script.skin.helper.widgets/fanart.jpg"},
                "isFolder": True,
                "type": "file",
                "IsPlayable": "false"
                }
         

        