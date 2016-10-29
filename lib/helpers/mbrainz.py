#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, formatted_number, log_msg, int_with_commas, try_parse_int, ADDON_ID, urlencode
from simplecache import use_cache
import datetime
import xbmc, xbmcvfs, xbmcaddon

class MusicBrainz(object):
    '''get metadata from musicbrainz'''
    
    def __init__(self, simplecache=None):
        '''Initialize - optionaly provide simplecache object'''
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
        import musicbrainzngs as mb
        mb.set_useragent("script.skin.helper.service", "1.0.0", "https://github.com/marcelveldt/script.skin.helper.service")
        mb.set_rate_limit(limit_or_interval=2.0, new_requests=1)
        addon = xbmcaddon.Addon(ADDON_ID)
        if addon.getSetting("music_art_mb_mirror"):
            mb.set_hostname(addon.getSetting("music_art_mb_mirror"))
        del addon
        self.mb = mb
    
    @use_cache(7)
    def search(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        mb_album = None
        albumid = ""
        artistid = ""
        artist = artist.lower()
        if not mb_album and artist and album:
            mb_albums = self.mb.search_release_groups(query=urlencode(album),
                limit=1, offset=None, strict=False, artist=urlencode(artist))
            if mb_albums and mb_albums.get("release-group-list"): 
                mb_album = mb_albums.get("release-group-list")[0]
        if not mb_album and artist and track:
            mb_albums = self.mb.search_recordings(query=urlencode(track), 
                limit=1, offset=None, strict=False, artist=urlencode(artist))
            if mb_albums and mb_albums.get("recording-list"): 
                mb_album = mb_albums.get("recording-list")[0]
        if mb_album:
            albumid = mb_album.get("id","")
            for mb_artist in mb_album.get("artist-credit"):
                if isinstance(mb_artist, dict) and mb_artist.get("artist",""):
                    #safety check - only allow exact artist match
                    foundartist = mb_artist.get("artist","").get("name")
                    if not isinstance(foundartist, unicode):
                        foundartist = foundartist.decode("utf-8")
                    foundartist = foundartist.lower()
                    if foundartist and (foundartist in artist or artist in foundartist):
                        artistid = mb_artist.get("artist").get("id")
                        break
        return (artistid, albumid)
        
    def get_artist_id(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        return self.search(artist, album, track)[0]
        
    def get_album_id(self, artist, album, track):
        '''get musicbrainz id by query of artist, album and/or track'''
        return self.search(artist, album, track)[1]
        
    def get_albumthumb(self, albumid):
        '''get album thumb'''
        thumb = ""
        try:
            thumbs_folder = "special://profile/addon_data/%s/musicthumbs/" %ADDON_ID
            if not xbmcvfs.exists(thumbs_folder):
                xbmcvfs.mkdir(thumbs_folder)
            thumb_file = "%s%s.jpg" %(thumbs_folder,albumid)
            thumb_data = self.mb.get_release_group_image_front(albumid)
            if thumb_data:
                f = xbmcvfs.File(thumb_file, 'w')
                f.write(thumbfile)
                f.close()
            thumb = thumb_file
        except Exception: 
            pass
        return thumb
                                
 