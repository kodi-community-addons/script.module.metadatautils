#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, formatted_number, log_msg, normalize_string, KODI_LANGUAGE
from simplecache import use_cache
import xbmcvfs

class TheAudioDb(object):
    '''get metadata from the audiodb'''
    base_url = 'http://www.theaudiodb.com/api/v1/json/32176f5352254d85853778/'
    
    def __init__(self, simplecache=None):
        '''Initialize - optionaly provide simplecache object'''
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
    
    def search(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        artistid = ""
        albumid = ""
        artist = artist.lower()
        params = {'s' : artist, 'a': album}
        data = self.getdata("searchalbum.php", params)
        if data and data.get("album") and len(data.get("album")) > 0:
            adbdetails = data["album"][0]
            #safety check - only allow exact artist match
            foundartist = adbdetails.get("strArtist","").lower()
            if foundartist and (foundartist in artist or artist in foundartist):
                albumid = adbdetails.get("strMusicBrainzID","")
                artistid = adbdetails.get("strMusicBrainzArtistID","")
        if (not artistid or not albumid) and artist and track:
            params = {'s' : artist, 't': track}
            data = self.getdata("searchtrack.php", params)
            if data and data.get("track") and len(data.get("track")) > 0:
                adbdetails = data["track"][0]
                #safety check - only allow exact artist match
                foundartist = adbdetails.get("strArtist","").lower()
                if foundartist and (foundartist in artist or artist in foundartist):
                    albumid = adbdetails.get("strMusicBrainzID","")
                    artistid = adbdetails.get("strMusicBrainzArtistID","")
        return (artistid, albumid)
        
    def get_artist_id(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        return self.search(artist, album, track)[0]
        
    def get_album_id(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        return self.search(artist, album, track)[1]
        
    @use_cache(60)
    def artist_info(self, artist_id):
        '''get artist metadata by musicbrainz id'''
        details = {"art": {} }
        data = self.getdata("/artist-mb.php", {'i' : artist_id} )
        if data and data.get("artists"):
            adbdetails = data["artists"][0]
            if adbdetails.get("strArtistBanner") and xbmcvfs.exists(adbdetails.get("strArtistBanner")): 
                details["art"]["banner"] = adbdetails.get("strArtistBanner")
                details["art"]["banners"] = [adbdetails.get("strArtistBanner")]
            details["art"]["fanarts"] = []
            if adbdetails.get("strArtistFanart") and xbmcvfs.exists(adbdetails.get("strArtistFanart")): 
                artwork["fanart"] = adbdetails.get("strArtistFanart")
                details["art"]["fanarts"].append(adbdetails.get("strArtistFanart"))
            if adbdetails.get("strArtistFanart2") and xbmcvfs.exists(adbdetails.get("strArtistFanart2")): 
                details["art"]["fanarts"].append(adbdetails.get("strArtistFanart2"))
            if adbdetails.get("strArtistFanart3") and xbmcvfs.exists(adbdetails.get("strArtistFanart3")): 
                details["art"]["fanarts"].append(adbdetails.get("strArtistFanart3"))
            if adbdetails.get("strArtistFanart4") and xbmcvfs.exists(adbdetails.get("strArtistFanart4")): 
                details["art"]["fanarts"].append(adbdetails.get("strArtistFanart4"))
            if adbdetails.get("strArtistLogo") and xbmcvfs.exists(adbdetails.get("strArtistLogo")): 
                details["art"]["clearlogo"] = adbdetails.get("strArtistLogo")
                details["art"]["clearlogos"] = [adbdetails.get("strArtistLogo")]
            if adbdetails.get("strArtistThumb") and xbmcvfs.exists(adbdetails.get("strArtistThumb")): 
                details["art"]["thumb"] = adbdetails["strArtistThumb"]
                details["art"]["thumbs"] = [adbdetails["strArtistThumb"]]
            if adbdetails.get("strBiography" + KODI_LANGUAGE.upper()): 
                details["plot"] = adbdetails["strBiography" + KODI_LANGUAGE.upper()]
            if adbdetails.get("strBiographyEN") and not details.get("plot"): 
                details["plot"] = adbdetails.get("strBiographyEN")
            if details.get("plot"): 
                details["plot"] = normalize_string(details["plot"].replace('\n', ' ').replace('\r', ''))
        return details
    
    @use_cache(60)
    def album_info(self, album_id):
        '''get album metadata by musicbrainz id'''
        details = {"art": {} }
        data = self.getdata("/album-mb.php", {'i' : album_id} )
        if data and data.get("album"):
            adbdetails = data["album"][0]
            if adbdetails.get("strAlbumThumb") and xbmcvfs.exists(adbdetails.get("strAlbumThumb")): 
                details["art"]["thumb"] = adbdetails.get("strAlbumThumb")
                details["art"]["thumbs"] = [adbdetails.get("strAlbumThumb")]
            if adbdetails.get("strAlbumCDart") and xbmcvfs.exists(adbdetails.get("strAlbumCDart")): 
                details["art"]["discart"] = adbdetails.get("strAlbumCDart")
                details["art"]["discarts"] = [adbdetails.get("strAlbumCDart")]
            if adbdetails.get("strDescription%s"%KODILANGUAGE.upper()): 
                details["plot"] = adbdetails.get("strDescription%s"%KODILANGUAGE.upper())
            if not details.get("plot") and adbdetails.get("strDescriptionEN"): 
                details["plot"] = adbdetails.get("strDescriptionEN")
            if details.get("plot"): 
                details["plot"] = normalize_string(details["plot"].replace('\n', ' ').replace('\r', ''))
        return details
        
    
    @use_cache(7)
    def get_data(self, endpoint, params):
        '''helper method to get data from theaudiodb json API'''
        endpoint = "%s%s" %(self.base_url,endpoint)
        data = get_json(endpoint, params)
        if data:
            return data
        else:
            return {}

  