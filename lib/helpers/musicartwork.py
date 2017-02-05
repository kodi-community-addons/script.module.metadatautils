#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.module.skin.helper.artutils
    musicartwork.py
    Get metadata for music
'''

from utils import log_msg, extend_dict, ADDON_ID, DialogSelect, strip_newlines, download_artwork
from mbrainz import MusicBrainz
from lastfm import LastFM
from theaudiodb import TheAudioDb
import os
import xbmc
import xbmcvfs
import xbmcgui
from urllib import quote_plus
from datetime import timedelta
from difflib import SequenceMatcher as SM
from simplecache import use_cache


class MusicArtwork(object):
    '''get metadata and artwork for music'''

    def __init__(self, artutils=None):
        '''Initialize - optionaly provide our base ArtUtils class'''
        if not artutils:
            from artutils import ArtUtils
            self.artutils = ArtUtils
        else:
            self.artutils = artutils
        self.cache = self.artutils.cache
        self.lastfm = LastFM()
        self.mbrainz = MusicBrainz()
        self.audiodb = TheAudioDb()

    @use_cache(14)
    def get_music_artwork(self, artist, album, track, disc, ignore_cache=False, flush_cache=False):
        '''get music metadata by providing artist and/or track'''
        artist_details = {"art": {}}
        feat_artist_details = {"art": {}}
        album_details = {}
        if artist == track or album == track:
            track = ""
        artists = self.get_all_artists(artist, track)
        album = self.get_clean_title(album)
        track = self.get_clean_title(track)
        # The first artist with details is considered the main artist
        # all others are assumed as featuring artists
        for artist in artists:
            if not (artist_details.get("plot") or artist_details.get("art")):
                # get main artist details
                artist_details = self.get_artist_metadata(
                    artist, album, track, ignore_cache=ignore_cache, flush_cache=flush_cache)
            else:
                # assume featuring artist
                feat_artist_details = extend_dict(
                    feat_artist_details, self.get_artist_metadata(
                        artist, album, track, ignore_cache=ignore_cache, flush_cache=flush_cache))
            if album or track and not (album_details.get("plot") or album_details.get("art")):
                album_details = self.get_album_metadata(
                    artist, album, track, disc, ignore_cache=ignore_cache, flush_cache=flush_cache)

        # flush cache returns blank result
        if flush_cache:
            return None

        # combine artist details and album details
        details = extend_dict(album_details, artist_details)

        # combine artist plot and album plot as extended plot
        if artist_details.get("plot") and album_details.get("plot"):
            details["extendedplot"] = "%s  --  %s" % (album_details["plot"], artist_details["plot"])
        else:
            details["extendedplot"] = details.get("plot", "")

        # append track title to results
        if track:
            details["title"] = track

        # combined images to use as multiimage (for all artists)
        # append featuring artist details
        for arttype in ["banners", "fanarts", "clearlogos", "thumbs"]:
            art = artist_details["art"].get(arttype, [])
            art += feat_artist_details["art"].get(arttype, [])
            if art:
                # use the extrafanart plugin entry to display multi images
                details["art"][arttype] = "plugin://script.skin.helper.service/"\
                    "?action=extrafanart&fanarts=%s" % quote_plus(repr(art))
        # set special extrafanart path if multiple artists
        # so we can have rotating fanart slideshow for all artists of the track
        if len(artists) > 1 and details.get("art").get("fanarts"):
            details["art"]["extrafanart"] = details["art"]["fanarts"]

        # return the endresult
        return details

    def manual_set_music_artwork(self, artist, album, track, disc):
        '''manual override artwork options'''
        details = {}
        artists = self.get_all_artists(artist, track)
        if len(artists) > 1:
            # multiple artists - user must select an artist
            header = self.artutils.addon.getLocalizedString(32015)
            dialog = xbmcgui.Dialog()
            ret = dialog.select(header, artists)
            del dialog
            if ret < 0:
                return
            clean_artist = artists[ret]
        else:
            clean_artist = artists[0]
        clean_album = self.get_clean_title(album)
        if artist == track or album == track:
            clean_track = ""
        else:
            clean_track = self.get_clean_title(track)
        details["artist"] = self.get_artist_metadata(clean_artist, clean_album, clean_track)
        art_types = {"artist": ["thumb", "poster", "fanart", "banner", "clearart", "clearlogo", "landscape"]}
        if album:
            details["album"] = self.get_album_metadata(clean_artist, clean_album, clean_track, disc)
            art_types["album"] = ["thumb", "discart"]

        changemade = False
        # show dialogselect with all artwork options
        abort = False
        while not abort:
            listitems = []
            for mediatype, arttypes in art_types.iteritems():
                for arttype in arttypes:
                    img = details[mediatype]["art"].get(arttype, "")
                    listitem = xbmcgui.ListItem(label=arttype, label2=mediatype, iconImage=img)
                    listitem.setProperty("icon", img)
                    listitem.setProperty("mediatype", mediatype)
                    listitems.append(listitem)
            dialog = DialogSelect("DialogSelect.xml", "", listing=listitems,
                                  window_title=xbmc.getLocalizedString(13511), multiselect=False)
            dialog.doModal()
            selected_item = dialog.result
            del dialog
            if selected_item == -1:
                abort = True
            else:
                # show results for selected art type
                artoptions = []
                selected_item = listitems[selected_item]
                image = selected_item.getProperty("icon").decode("utf-8")
                mediatype = selected_item.getProperty("mediatype").decode("utf-8")
                label = selected_item.getLabel().decode("utf-8")
                heading = "%s: %s" % (xbmc.getLocalizedString(13511), label)
                if image:
                    # current image
                    listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(13512), iconImage=image, label2=image)
                    listitem.setProperty("icon", image)
                    artoptions.append(listitem)
                    # none option
                    listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(231), iconImage="DefaultAddonNone.png")
                    listitem.setProperty("icon", "DefaultAddonNone.png")
                    artoptions.append(listitem)
                # browse option
                listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(1024), iconImage="DefaultFolder.png")
                listitem.setProperty("icon", "DefaultFolder.png")
                artoptions.append(listitem)

                # add remaining images as option
                allarts = details[mediatype]["art"].get(label + "s", [])
                if len(allarts) > 1:
                    for item in allarts:
                        listitem = xbmcgui.ListItem(label=item, iconImage=item)
                        listitem.setProperty("icon", item)
                        artoptions.append(listitem)

                dialog = DialogSelect("DialogSelect.xml", "", listing=artoptions, window_title=heading)
                dialog.doModal()
                selected_item = dialog.result
                del dialog
                if image and selected_item == 1:
                    details[mediatype]["art"][label] = ""
                    changemade = True
                elif image and selected_item > 2:
                    details[mediatype]["art"][label] = artoptions[selected_item].getProperty("icon")
                    changemade = True
                elif (image and selected_item == 2) or not image and selected_item == 0:
                    # manual browse...
                    dialog = xbmcgui.Dialog()
                    image = dialog.browse(2, xbmc.getLocalizedString(1030),
                                          'files', mask='.gif|.png|.jpg').decode("utf-8")
                    del dialog
                    if image:
                        details[mediatype]["art"][label] = image
                        changemade = True

        # save results if any changes made
        if changemade:
            refresh_needed = False
            download_art = self.artutils.addon.getSetting("music_art_download") == "true"
            download_art_custom = self.artutils.addon.getSetting("music_art_download_custom") == "true"
            for mediatype in art_types.iterkeys():
                # download artwork to music folder if needed
                if details[mediatype].get("diskpath") and download_art:
                    details[mediatype]["art"] = download_artwork(
                        details[mediatype]["diskpath"], details[mediatype]["art"])
                    refresh_needed = True
                # download artwork to custom folder if needed
                if details[mediatype].get("customartpath") and download_art_custom:
                    details[mediatype]["art"] = download_artwork(
                        details[mediatype]["customartpath"], details[mediatype]["art"])
                    refresh_needed = True
                # correct artistthumb/albumthumb
                details[mediatype]["art"]["%s" % mediatype] = details[mediatype]["art"].get("thumb", "")
                # save new values to cache
                self.artutils.cache.set(
                    details[mediatype]["cachestr"],
                    details[mediatype],
                    expiration=timedelta(days=120))
            # flush musicart cache
            self.get_music_artwork(artist, album, track, disc, ignore_cache=True, flush_cache=True)
            # reload skin to make sure new artwork is visible
            if refresh_needed:
                xbmc.sleep(500)
                xbmc.executebuiltin("ReloadSkin()")

    def music_artwork_options(self, artist, album, track, disc):
        '''show options for music artwork'''
        options = []
        options.append(self.artutils.addon.getLocalizedString(32028))  # Refresh item (auto lookup)
        options.append(self.artutils.addon.getLocalizedString(32036))  # Choose art
        options.append(self.artutils.addon.getLocalizedString(32034))  # Open addon settings
        header = self.artutils.addon.getLocalizedString(32015)
        dialog = xbmcgui.Dialog()
        ret = dialog.select(header, options)
        del dialog
        if ret == 0:
            # Refresh item (auto lookup)
            self.artutils.fanarttv.ignore_cache = True
            self.audiodb.ignore_cache = True
            self.mbrainz.ignore_cache = True
            self.lastfm.ignore_cache = True
            self.get_music_artwork(artist, album, track, disc, ignore_cache=True)
        elif ret == 1:
            # Choose art
            self.manual_set_music_artwork(artist, album, track, disc)
        elif ret == 2:
            # Open addon settings
            xbmc.executebuiltin("Addon.OpenSettings(%s)" % ADDON_ID)

    def get_artist_metadata(self, artist, album, track, ignore_cache=False, flush_cache=False):
        '''collect artist metadata'''
        artists = self.get_all_artists(artist, track)
        album = self.get_clean_title(album)
        track = self.get_clean_title(track)
        artist = artists[0]
        cache_str = "music_artwork.artist.%s" % artist.lower()
        cache = self.artutils.cache.get(cache_str)
        if flush_cache:
            self.artutils.cache.set(cache_str, None)
            return {"art": {}}
        if cache and not ignore_cache:
            return cache

        log_msg("get_artist_metadata --> artist: %s - album: %s - track: %s" % (artist, album, track))

        details = {"art": {}}
        details["cachestr"] = cache_str
        local_path = ""
        local_path_custom = ""
        # get metadata from kodi db
        details = extend_dict(details, self.get_artist_kodi_metadata(artist))
        # get artwork from songlevel path
        if details.get("diskpath") and self.artutils.addon.getSetting("music_art_musicfolders") == "true":
            details["art"] = extend_dict(details["art"], self.lookup_artistart_in_folder(details["diskpath"]))
            local_path = details["diskpath"]
        # get artwork from custom folder
        if self.artutils.addon.getSetting("music_art_custom") == "true":
            custom_path = self.artutils.addon.getSetting("music_art_custom_path").decode("utf-8")
            if custom_path:
                diskpath = self.get_customfolder_path(custom_path, artist)
                log_msg("custom path on disk for artist: %s --> %s" % (artist, diskpath))
                if diskpath:
                    details["art"] = extend_dict(details["art"], self.lookup_artistart_in_folder(diskpath))
                    local_path_custom = diskpath
                    details["customartpath"] = diskpath
        # lookup online metadata
        if self.artutils.addon.getSetting("music_art_scraper") == "true":
            if not album and not track:
                album = details.get("ref_album")
                track = details.get("ref_track")
            mb_artistid = details.get("musicbrainzartistid", self.get_mb_artist_id(artist, album, track))
            if mb_artistid:
                # get artwork from fanarttv
                if self.artutils.addon.getSetting("music_art_scraper_fatv") == "true":
                    details["art"] = extend_dict(details["art"], self.artutils.fanarttv.artist(mb_artistid))
                # get metadata from theaudiodb
                if self.artutils.addon.getSetting("music_art_scraper_adb") == "true":
                    details = extend_dict(details, self.audiodb.artist_info(mb_artistid))
                # get metadata from lastfm
                if self.artutils.addon.getSetting("music_art_scraper_lfm") == "true":
                    details = extend_dict(details, self.lastfm.artist_info(mb_artistid))

                # download artwork to music folder
                if local_path and self.artutils.addon.getSetting("music_art_download") == "true":
                    details["art"] = download_artwork(local_path, details["art"])
                # download artwork to custom folder
                if local_path_custom and self.artutils.addon.getSetting("music_art_download_custom") == "true":
                    details["art"] = download_artwork(local_path_custom, details["art"])

                # fix extrafanart
                if details["art"].get("fanarts"):
                    for count, item in enumerate(details["art"]["fanarts"]):
                        details["art"]["fanart.%s" % count] = item
                    if not details["art"].get("extrafanart") and len(details["art"]["fanarts"]) > 1:
                        details["art"]["extrafanart"] = "plugin://script.skin.helper.service/"\
                            "?action=extrafanart&fanarts=%s" % quote_plus(repr(details["art"]["fanarts"]))

        # set default details
        if not details.get("artist"):
            details["artist"] = artist
        if details["art"].get("thumb"):
            details["art"]["artistthumb"] = details["art"]["thumb"]
        details["musicbrainzartistid"] = mb_artistid

        # store results in cache and return results
        self.artutils.cache.set(cache_str, details)
        return details

    def get_album_metadata(self, artist, album, track, disc, ignore_cache=False, flush_cache=False):
        '''collect all album metadata'''

        cache_str = "music_artwork.album.%s.%s.%s" % (artist.lower(), album.lower(), disc.lower())
        if not album and track:
            cache_str = "music_artwork.album.%s.%s" % (artist.lower(), track.lower())
        cache = self.artutils.cache.get(cache_str)
        if flush_cache:
            self.artutils.cache.set(cache_str, None)
            return {"art": {}}
        if cache and not ignore_cache:
            return cache

        details = {"art": {}}
        details["cachestr"] = cache_str
        local_path = ""
        local_path_custom = ""
        # get metadata from kodi db
        details = extend_dict(details, self.get_album_kodi_metadata(artist, album, track, disc))
        # get artwork from songlevel path
        if details.get("diskpath") and self.artutils.addon.getSetting("music_art_musicfolders") == "true":
            details["art"] = extend_dict(details["art"], self.lookup_albumart_in_folder(details["diskpath"]))
            local_path = details["diskpath"]
        # get artwork from custom folder
        if self.artutils.addon.getSetting("music_art_custom") == "true":
            custom_path = self.artutils.addon.getSetting("music_art_custom_path").decode("utf-8")
            if custom_path:
                diskpath = self.get_custom_album_path(custom_path, artist, album, disc)
                if diskpath:
                    details["art"] = extend_dict(details["art"], self.lookup_albumart_in_folder(diskpath))
                    local_path_custom = diskpath
                    details["customartpath"] = diskpath
        # lookup online metadata
        if self.artutils.addon.getSetting("music_art_scraper") == "true":
            mb_albumid = details.get("musicbrainzalbumid")
            if not mb_albumid:
                mb_albumid = self.get_mb_album_id(artist, album, track)
            if mb_albumid:
                # get artwork from fanarttv
                if self.artutils.addon.getSetting("music_art_scraper_fatv") == "true":
                    details["art"] = extend_dict(details["art"], self.artutils.fanarttv.album(mb_albumid))
                # get metadata from theaudiodb
                if self.artutils.addon.getSetting("music_art_scraper_adb") == "true":
                    details = extend_dict(details, self.audiodb.album_info(mb_albumid))
                # get metadata from lastfm
                if self.artutils.addon.getSetting("music_art_scraper_lfm") == "true":
                    details = extend_dict(details, self.lastfm.album_info(mb_albumid))
                # metadata from musicbrainz
                if not details.get("year") or not details.get("genre"):
                    details = extend_dict(details, self.mbrainz.get_albuminfo(mb_albumid))
                # musicbrainz thumb as last resort
                if not details["art"].get("thumb"):
                    details["art"]["thumb"] = self.mbrainz.get_albumthumb(mb_albumid)
                # download artwork to music folder
                if local_path and self.artutils.addon.getSetting("music_art_download") == "true":
                    details["art"] = download_artwork(local_path, details["art"])
                # download artwork to custom folder
                if local_path_custom and self.artutils.addon.getSetting("music_art_download_custom") == "true":
                    details["art"] = download_artwork(local_path_custom, details["art"])

        # set default details
        if not details.get("album") and details.get("title"):
            details["album"] = details["title"]
        if details["art"].get("thumb"):
            details["art"]["albumthumb"] = details["art"]["thumb"]

        # store results in cache and return results
        self.artutils.cache.set(cache_str, details)
        return details

    def get_artist_kodi_metadata(self, artist):
        '''get artist details from the kodi database'''
        details = {}
        filters = [{"operator": "is", "field": "artist", "value": artist}]
        result = self.artutils.kodidb.artists(filters=filters, limits=(0, 1))
        if result:
            details = result[0]
            details["title"] = details["artist"]
            details["plot"] = strip_newlines(details["description"])
            if details["musicbrainzartistid"] and isinstance(details["musicbrainzartistid"], list):
                details["musicbrainzartistid"] = details["musicbrainzartistid"][0]
            filters = [{"artistid": details["artistid"]}]
            artist_albums = self.artutils.kodidb.albums(filters=filters)
            details["albums"] = []
            details["albumsartist"] = []
            details["albumscompilations"] = []
            details["tracks"] = []
            bullet = "•".decode("utf-8")
            details["albums.formatted"] = u""
            details["tracks.formatted"] = u""
            details["tracks.formatted2"] = u""
            details["albumsartist.formatted"] = u""
            details["albumscompilations.formatted"] = u""
            # enumerate albums for this artist
            for artist_album in artist_albums:
                details["albums"].append(artist_album["label"])
                details["albums.formatted"] += u"%s %s [CR]" % (bullet, artist_album["label"])
                if artist in artist_album["displayartist"]:
                    details["albumsartist"].append(artist_album["label"])
                    details["albumsartist.formatted"] += u"%s %s [CR]" % (bullet, artist_album["label"])
                else:
                    details["albumscompilations"].append(artist_album["label"])
                    details["albumscompilations.formatted"] += u"%s %s [CR]" % (bullet, artist_album["label"])
                # enumerate songs for this album
                filters = [{"albumid": artist_album["albumid"]}]
                album_tracks = self.artutils.kodidb.songs(filters=filters)
                if album_tracks:
                    # retrieve path on disk by selecting one song for this artist
                    if not details.get("ref_track") and not len(artist_album["artistid"]) > 1:
                        song_path = album_tracks[0]["file"]
                        details["diskpath"] = self.get_artistpath_by_songpath(song_path, artist)
                        details["ref_album"] = artist_album["title"]
                        details["ref_track"] = album_tracks[0]["title"]
                    for album_track in album_tracks:
                        details["tracks"].append(album_track["title"])
                        tr_title = album_track["title"]
                        if album_track["track"]:
                            tr_title = "%s. %s" % (album_track["track"], album_track["title"])
                        details["tracks.formatted"] += u"%s %s [CR]" % (bullet, tr_title)
                        duration = album_track["duration"]
                        total_seconds = int(duration)
                        minutes = total_seconds / 60
                        seconds = total_seconds - (minutes * 60)
                        duration = "%s:%s" % (minutes, str(seconds).zfill(2))
                        details["tracks.formatted2"] += u"%s %s (%s)[CR]" % (bullet, tr_title, duration)
            details["albumcount"] = len(details["albums"])
            details["albumsartistcount"] = len(details["albumsartist"])
            details["albumscompilationscount"] = len(details["albumscompilations"])
            # do not retrieve artwork from item as there's no way to write it back
            # and it will already be retrieved if user enables to get the artwork from the song path
        return details

    def get_album_kodi_metadata(self, artist, album, track, disc):
        '''get album details from the kodi database'''
        details = {}
        filters = [{"operator": "is", "field": "album", "value": album}]
        filters.append({"operator": "is", "field": "artist", "value": artist})
        if artist and track and not album:
            # get album by track
            result = self.artutils.kodidb.songs(filters=filters)
            for item in result:
                album = item["album"]
                break
        if artist and album:
            result = self.artutils.kodidb.albums(filters=filters)
            if result:
                details = result[0]
                details["plot"] = strip_newlines(details["description"])
                filters = [{"albumid": details["albumid"]}]
                album_tracks = self.artutils.kodidb.songs(filters=filters)
                details["tracks"] = []
                bullet = "•".decode("utf-8")
                details["tracks.formatted"] = u""
                details["tracks.formatted2"] = ""
                details["runtime"] = 0
                for item in album_tracks:
                    details["tracks"].append(item["title"])
                    details["tracks.formatted"] += u"%s %s [CR]" % (bullet, item["title"])
                    duration = item["duration"]
                    total_seconds = int(duration)
                    minutes = total_seconds / 60
                    seconds = total_seconds - (minutes * 60)
                    duration = "%s:%s" % (minutes, str(seconds).zfill(2))
                    details["runtime"] += item["duration"]
                    details["tracks.formatted2"] += u"%s %s (%s)[CR]" % (bullet, item["title"], duration)
                    if not details.get("diskpath"):
                        if not disc or item["disc"] == int(disc):
                            details["diskpath"] = self.get_albumpath_by_songpath(item["file"])
                details["art"] = {}
                details["songcount"] = len(album_tracks)
                # get album total duration pretty printed as mm:ss
                total_seconds = int(details["runtime"])
                minutes = total_seconds / 60
                seconds = total_seconds - (minutes * 60)
                details["duration"] = "%s:%s" % (minutes, str(seconds).zfill(2))
                # do not retrieve artwork from item as there's no way to write it back
                # and it will already be retrieved if user enables to get the artwork from the song path
        return details

    def get_mb_artist_id(self, artist, album, track):
        '''lookup musicbrainz artist id with query of artist and album/track'''
        artistid = self.mbrainz.get_artist_id(artist, album, track)
        if not artistid and self.artutils.addon.getSetting("music_art_scraper_lfm") == "true":
            artistid = self.lastfm.get_artist_id(artist, album, track)
        if not artistid and self.artutils.addon.getSetting("music_art_scraper_adb") == "true":
            artistid = self.audiodb.get_artist_id(artist, album, track)
        return artistid

    def get_mb_album_id(self, artist, album, track):
        '''lookup musicbrainz album id with query of artist and album/track'''
        albumid = self.mbrainz.get_album_id(artist, album, track)
        if not albumid and self.artutils.addon.getSetting("music_art_scraper_lfm") == "true":
            albumid = self.lastfm.get_album_id(artist, album, track)
        if not albumid and self.artutils.addon.getSetting("music_art_scraper_adb") == "true":
            albumid = self.audiodb.get_album_id(artist, album, track)
        return albumid

    @staticmethod
    def get_artistpath_by_songpath(songpath, artist):
        '''get the artist path on disk by listing the song's path'''
        result = ""
        if "\\" in songpath:
            delim = "\\"
        else:
            delim = "/"
        # just move up the directory tree (max 3 levels) untill we find the directory
        for trypath in [songpath.rsplit(delim, 2)[0] + delim,
                        songpath.rsplit(delim, 3)[0] + delim, songpath.rsplit(delim, 1)[0] + delim]:
            if trypath.split(delim)[-2].lower() == artist.lower():
                result = trypath
                break
        return result

    @staticmethod
    def get_albumpath_by_songpath(songpath):
        '''get the album path on disk by listing the song's path'''
        if "\\" in songpath:
            delim = "\\"
        else:
            delim = "/"
        return songpath.rsplit(delim, 1)[0] + delim

    @staticmethod
    def lookup_artistart_in_folder(folderpath):
        '''lookup artwork in given folder'''
        artwork = {}
        files = xbmcvfs.listdir(folderpath)[1]
        for item in files:
            item = item.decode("utf-8")
            if item in ["banner.jpg", "clearart.png", "poster.png", "fanart.jpg", "landscape.jpg"]:
                key = item.split(".")[0]
                artwork[key] = folderpath + item
            elif item == "logo.png":
                artwork["clearlogo"] = folderpath + item
            elif item == "folder.jpg":
                artwork["thumb"] = folderpath + item
        # extrafanarts
        efa_path = folderpath + "extrafanart/"
        if xbmcvfs.exists(efa_path):
            files = xbmcvfs.listdir(efa_path)[1]
            artwork["fanarts"] = []
            if files:
                artwork["extrafanart"] = efa_path
                for item in files:
                    item = efa_path + item.decode("utf-8")
                    artwork["fanarts"].append(item)
        return artwork

    @staticmethod
    def lookup_albumart_in_folder(folderpath):
        '''lookup artwork in given folder'''
        artwork = {}
        files = xbmcvfs.listdir(folderpath)[1]
        for item in files:
            item = item.decode("utf-8")
            if item in ["cdart.png", "disc.png"]:
                artwork["discart"] = folderpath + item
            elif item == "folder.jpg":
                artwork["thumb"] = folderpath + item
        return artwork

    def get_custom_album_path(self, custom_path, artist, album, disc):
        '''try to locate the custom path for the album'''
        artist_path = self.get_customfolder_path(custom_path, artist)
        album_path = ""
        if artist_path:
            album_path = self.get_customfolder_path(artist_path, album)
            if album_path and disc:
                if "\\" in album_path:
                    delim = "\\"
                else:
                    delim = "/"
                dirs = xbmcvfs.listdir(album_path)[0]
                for directory in dirs:
                    directory = directory.decode("utf-8")
                    if disc in directory:
                        return os.path.join(album_path, directory) + delim
        return album_path

    def get_customfolder_path(self, customfolder, foldername, sublevel=False):
        '''search recursively (max 2 levels) for a specific folder'''
        cachestr = "customfolder_path.%s.%s" % (customfolder, foldername)
        folder_path = self.cache.get(cachestr)
        if not folder_path:
            if "\\" in customfolder:
                delim = "\\"
            else:
                delim = "/"
            dirs = xbmcvfs.listdir(customfolder)[0]
            for strictness in [1, 0.95, 0.9, 0.8]:
                for directory in dirs:
                    directory = directory.decode("utf-8")
                    curpath = os.path.join(customfolder, directory) + delim
                    match = SM(None, foldername.lower(), directory.lower()).ratio()
                    if match >= strictness:
                        folder_path = curpath
                    elif not sublevel:
                        # check if our requested path is in a sublevel of the current path
                        # restrict the number of sublevels to just one for now for performance reasons
                        folder_path = self.get_customfolder_path(curpath, foldername, True)
                    if folder_path:
                        break
                if folder_path:
                    break
            if not sublevel:
                self.cache.set(cachestr, folder_path)
        return folder_path

    @staticmethod
    def get_clean_title(title):
        '''strip all unwanted characters from track name'''
        title = title.split("/")[0]
        title = title.split("(")[0]
        title = title.split("[")[0]
        title = title.split("ft.")[0]
        title = title.split("Ft.")[0]
        title = title.split("Feat.")[0]
        title = title.split("Featuring")[0]
        title = title.split("featuring")[0]
        return title.strip()

    @staticmethod
    def get_all_artists(artist, track):
        '''extract multiple artists from both artist and track string'''
        artists = []
        feat_artists = []

        # fix for band names which actually contain the kodi splitter (slash) in their name...
        specials = ["AC/DC"]  # to be completed with more artists
        for special in specials:
            if special in artist:
                artist = artist.replace(special, special.replace("/", ""))

        for splitter in ["ft.", "feat.", "featuring", "Ft.", "Feat.", "Featuring"]:
            # replace splitter by kodi default splitter for easier split all later
            artist = artist.replace(splitter, u"/")

            # extract any featuring artists from trackname
            if splitter in track:
                track_parts = track.split(splitter)
                if len(track_parts) > 1:
                    feat_artist = track_parts[1].replace(")", "").replace("(", "").strip()
                    feat_artists.append(feat_artist)

        # break all artists string into list
        all_artists = artist.split("/") + feat_artists
        for item in all_artists:
            item = item.strip()
            if not item in artists:
                artists.append(item)
            # & can be a both a splitter or part of artist name
            for item2 in item.split("&"):
                item2 = item2.strip()
                if not item2 in artists:
                    artists.append(item2)
        return artists
