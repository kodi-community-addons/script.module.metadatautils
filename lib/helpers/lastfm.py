#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, formatted_number, log_msg, int_with_commas, normalize_string
from simplecache import use_cache
import xbmcvfs

class LastFM(object):
    '''get metadata from the lastfm'''
    
    def __init__(self, simplecache=None):
        '''Initialize - optionaly provide simplecache object'''
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
    
    @use_cache(7)
    def search(self, artist, album, track):
        '''get musicbrainz id's by query of artist, album and/or track'''
        artistid = ""
        albumid = ""
        artist = artist.lower()
        params = {'method': 'album.getInfo', 'artist' : artist, 'album': album}
        data = self.get_data(params)
        if data and data.get("album"):
            lfmdetails = data["album"]
            if lfmdetails.get("mbid"): 
                albumid = lfmdetails.get("mbid")
            if lfmdetails.get("tracks") and lfmdetails["tracks"].get("track"):
                for track in lfmdetails.get("tracks")["track"]:
                    if track["artist"]["name"].lower() == artist and track["artist"]["mbid"]:
                        artistid = track["artist"]["mbid"]
                        break
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
        details = { "art": {} }
        details["art"]["thumbs"] = []
        params = {'method': 'artist.getInfo', 'mbid': artist_id}
        data = self.get_data(params)
        if data and data.get("artist"):
            lfmdetails = data["artist"]
            if lfmdetails.get("image"):
                for image in lfmdetails["image"]:
                    if image and image["size"] == "extralarge" and xbmcvfs.exists(image["#text"]): 
                        details["art"]["thumbs"].append(image["#text"])
                        if not details["art"].get("thumb"):
                            details["art"]["thumb"].append(image["#text"])
            if lfmdetails.get("bio"): 
                details["plot"] = normalize_string(lfmdetails["bio"].get("content","").split(' <a href')[0])
        return details
        
    @use_cache(60)
    def album_info(self, album_id):
        '''get album metadata by musicbrainz id'''
        details = { "art": {} }
        details["art"]["thumbs"] = []
        params = {'method': 'album.getInfo', 'mbid': album_id}
        data = self.get_data(params)
        if data and data.get("album"):
            if isinstance(data["album"], list): 
                lfmdetails = data["album"][0]
            else: 
                lfmdetails = data["album"]
            if lfmdetails.get("image"):
                for image in lfmdetails["image"]:
                    if image and image["size"] == "extralarge" and xbmcvfs.exists(image["#text"]): 
                        details["art"]["thumbs"].append(image["#text"])
                        if not details["art"].get("thumb"):
                            details["art"]["thumb"].append(image["#text"])

            if lfmdetails.get("wiki"): 
                details["plot"] = normalize_string(lfmdetails["wiki"].get("content","").split(' <a')[0])
    
        
    @use_cache(7)
    def get_data(self, params):
        '''helper method to get data from lastfm json API'''
        params["format"] = "json"
        params["api_key"] = "822eb03d95f45fbab2137d646aaf798"
        data = get_json('http://ws.audioscrobbler.com/2.0/', params)
        if data:
            return data
        else:
            return {}

  