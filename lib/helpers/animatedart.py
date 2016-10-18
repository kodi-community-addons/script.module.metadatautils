#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, DialogSelect, log_msg
from kodidb import KodiDb
import xbmc, xbmcvfs, xbmcgui
from simplecache import SimpleCache, use_cache



class AnimatedArt(object):
    '''get animated artwork'''
    
    cache = SimpleCache()

    def __init__(self, *args):
        self.kodidb = KodiDb()
    
    def get_animated_artwork(self,imdb_id,manual_select=False):
        '''returns both the animated poster and fanart for use in kodi'''
        if manual_select:
            xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        #no cache so grab the results
        result = {
            "animatedposter": self.poster(imdb_id, manual_select),
            "animatedfanart": self.fanart(imdb_id, manual_select),
            "imdb_id": imdb_id
            }
        self.write_kodidb(result)
        if manual_select:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        return result
        
    def poster(self,imdb_id,manual_select=False):
        '''return preferred animated poster, optionally show selectdialog for manual selection'''
        img = self.select_art(self.posters(imdb_id),manual_select)
        return self.process_image(img,"poster",imdb_id)

    def fanart(self,imdb_id,manual_select=False):
        '''return preferred animated fanart, optionally show selectdialog for manual selection'''
        img = self.select_art(self.fanarts(imdb_id),manual_select)
        return self.process_image(img,"fanart",imdb_id)
        
    def posters(self,imdb_id):
        '''return all animated posters for the given imdb_id (imdbid can also be tmdbid)'''
        return self.get_art(imdb_id,"posters")
        
    def fanarts(self,imdb_id):
        '''return animated fanarts for the given imdb_id (imdbid can also be tmdbid)'''
        return self.get_art(imdb_id,"fanarts")
        
    def get_art(self,imdb_id,art_type):
        '''get the artwork'''
        art_db = self.get_animatedart_db()
        if art_db.get(imdb_id):
            return art_db[imdb_id][art_type]
        return []
    
    @use_cache(7)
    def get_animatedart_db(self):
        '''get the full animated art database as dict with imdbid and tmdbid as key - uses 7 day cache to prevent overloading the server'''
        #get all animated posters from the online json file
        art_db = {}
        data = get_json('http://www.consiliumb.com/animatedgifs/movies.json',None,0)
        base_url = data.get("baseURL","")
        if data and data.get('movies'):
            for item in data['movies']:
                for db_id in ["imdbid","tmdbid"]:
                    key = item[db_id]
                    art_db[key] = { "posters": [], "fanarts": []}
                    for entry in item['entries']:
                        entry_new = {
                            "contributedby": entry["contributedBy"], 
                            "dateadded": entry["dateAdded"], 
                            "language": entry["language"],
                            "source":entry["source"],
                            "image": "%s/%s" %(base_url,entry["image"].replace(".gif","_original.gif")),
                            "thumb": "%s/%s" %(base_url,entry["image"])}
                        if entry['type'] == 'poster':
                            art_db[key]["posters"].append( entry_new )
                        elif entry['type'] == 'background':
                            art_db[key]["fanarts"].append( entry_new )
        return art_db
    
    @staticmethod
    def select_art(items,manual_select=False):
        '''select the preferred image from the list'''
        image = None
        if manual_select:
            #show selectdialog to manually select the item
            results_list = []
            art_type = ""
            #add none and browse entries
            listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(231),iconImage="DefaultAddonNone.png")
            results_list.append(listitem)
            listitem = xbmcgui.ListItem(label=xbmc.getLocalizedString(1030),iconImage="DefaultFolder.png")
            results_list.append(listitem)
            for item in items:
                labels = [item["contributedby"],item["dateadded"],item["language"],item["source"]]
                label = " / ".join(labels)
                art_type = "poster" 
                if "background" in item["image"]:
                    art_type = "fanart"
                listitem = xbmcgui.ListItem(label=label,iconImage=item["thumb"])
                results_list.append(listitem)
                #TODO: also add manual browse option!
            if manual_select and results_list:
                w = DialogSelect( "DialogSelect.xml", "", listing=results_list, window_title=art_type )
                w.doModal()
                selected_item = w.result
                if selected_item == 1:
                    #browse for image
                    image = xbmcgui.Dialog().browse( 2 , xbmc.getLocalizedString(1030), 'files', mask='.gif').decode("utf-8")
                elif selected_item > 1:
                    #user has selected an image from online results
                    image = items[selected_item-2]["image"]
        elif items:
            #just grab the first item as best match
            image = items[0]["image"]
        return image
        
    @staticmethod
    def process_image(image_url, art_type, imdb_id):
        '''animated gifs need to be stored locally, otherwise they won't work'''
        #make sure that our local path for the gif images exists
        if not xbmcvfs.exists("special://thumbnails/animatedgifs/"):
            xbmcvfs.mkdir("special://thumbnails/animatedgifs/")
        #only process existing images
        if not image_url or not xbmcvfs.exists(image_url):
            return None
        #copy the image to our local path and return the new path as value
        local_filename = "special://thumbnails/animatedgifs/%s_%s.gif" %(imdb_id,art_type)
        if xbmcvfs.exists(local_filename):
            xbmcvfs.delete(local_filename)
        #we don't use xbmcvfs.copy because we want to wait for the action to complete
        img = xbmcvfs.File(image_url)
        img_data = img.readBytes()
        img.close()
        img = xbmcvfs.File(local_filename,'w')
        img.write(img_data)
        img.close()
        return local_filename
        
    def write_kodidb(self,artwork):
        '''store the animated artwork in kodi database to access it with ListItem.Art(animatedartX)'''
        filters = [{ "operator":"is", "field":"imdbnumber", "value":artwork["imdb_id"]}]
        kodi_movies = self.kodidb.movies(filters=filters)
        if kodi_movies:
            kodi_movie = kodi_movies[0]
            cur_poster = kodi_movie["art"].get("animatedposter","")
            cur_fanart = kodi_movie["art"].get("animatedfanart","")
            #only perform write if there are changes
            if cur_poster != artwork["animatedposter"] or cur_fanart != artwork["animatedfanart"]:
                params = {
                    "movieid": kodi_movie["movieid"],
                    "art": {"animatedfanart": artwork["animatedfanart"], "animatedposter": artwork["animatedposter"]}
                    }
                self.kodidb.set_kodi_json('VideoLibrary.SetMovieDetails', params)
            
            