#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, KODI_LANGUAGE, rate_limiter
from operator import itemgetter

class Tmdb(object):
    '''get metadata from tmdb'''
    
    def search_movie(self,title,year="",manual_select=False):
        '''
            Search tmdb for a specific movie, returns full details of best match
            parameters:
            title: (required) the title of the movie to search for
            year: (optional) the year of the movie to search for (enhances search result if supplied)
            manual_select: (optional) if True will show select dialog with all results
        '''
        details = self.select_best_match(self.search_movies(title,year), manual_select)
        if details:
            details = self.get_movie_details(details["id"])
        return details
        
    def search_tvshow(self,title,year="",manual_select=False):
        '''
            Search tmdb for a specific movie, returns full details of best match
            parameters:
            title: (required) the title of the movie to search for
            year: (optional) the year of the movie to search for (enhances search result if supplied)
            manual_select: (optional) if True will show select dialog with all results
        '''
        details = self.select_best_match(self.search_movies(title,year), manual_select)
        if details:
            details = self.get_movie_details(details["id"])
        return details
        
    def search_video(self,title,year="",manual_select=False):
        '''
            Search tmdb for a specific entry (can be movie or tvshow), returns full details of best match
            parameters:
            title: (required) the title of the movie/tvshow to search for
            year: (optional) the year of the media to search for (enhances search result if supplied)
            manual_select: (optional) if True will show select dialog with all results
        '''
        details = self.select_best_match(self.search_videos(title,year), manual_select)
        if details and details["media_type"] == "movie":
            details = self.get_movie_details(details["id"])
        elif details and details["media_type"] == "tv":
            details = self.get_tvshow_details(details["id"])
        return details

    def search_videos(self,title,year=""):
        '''
            Search tmdb for a specific entry (can be movie or tvshow), parameters:
            title: (required) the title of the movie/tvshow to search for
            year: (optional) the year of the media to search for (enhances search result if supplied)
        '''
        params = {"query": title, "language": KODI_LANGUAGE}
        data = self.get_data("search/multi",params)
        if data and year:
            #prefer result with correct year if year is supplied
            newdata = []
            for item in data:
                if item.get("first_air_date") and year in item["first_air_date"]:
                    newdata.append(item)
                elif item.get("release_date") and year in item["release_date"]:
                    newdata.append(item)
            if newdata:
                data = newdata
        return data

    def search_movies(self,title,year=""):
        '''
            Search tmdb for a specific movie, returns a list of all closest matches
            parameters:
            title: (required) the title of the movie to search for
            year: (optional) the year of the movie to search for (enhances search result if supplied)
        '''
        params = {"query": title, "language": KODI_LANGUAGE}
        if year:
            params["year"] = int(year)
        return self.get_data("search/movie",params)

    def search_tvshows(self,title,year=""):
        '''
            Search tmdb for a specific tvshow, returns a list of all closest matches
            parameters:
            title: (required) the title of the tvshow to search for
            year: (optional) the first air date year of the tvshow to search for (enhances search result if supplied)
        '''
        params = {"query": title, "language": KODI_LANGUAGE}
        if year:
            params["first_air_date_year"] = int(year)
        return self.get_data("search/tv",params)

    def get_actor(self,name):
        '''
            Search tmdb for a specific actor/person, returns the best match as kodi compatible dict
            required parameter: name --> the name of the person
        '''
        params = {"query": name, "language": KODI_LANGUAGE}
        result =  self.get_data("search/person",params)
        if result:
            result = result[0]
            cast_thumb = "http://image.tmdb.org/t/p/original%s"%result["profile_path"] if result["profile_path"] else ""
            item = {"name": result["name"], 
                "thumb": cast_thumb,
                "roles": [item["title"] if item.get("title") else item["name"] for item in result["known_for"]] }
            return item
        else:
            return {}
                
    def get_movie_details(self,movie_id):
        '''get all moviedetails'''
        params = {
            "append_to_response": "keywords,videos,credits,images", 
            "include_image_language": "%s,en"%KODI_LANGUAGE,
            "language": KODI_LANGUAGE
            }
        details = self.map_details(self.get_data("movie/%s"%movie_id,params),"movie")
        return details
        
    def get_tvshow_details(self,tvshow_id):
        '''get all tvshowdetails'''
        params = {
            "append_to_response": "keywords,videos,external_ids,credits,images", 
            "include_image_language": "%s,en"%KODI_LANGUAGE,
            "language": KODI_LANGUAGE
            }
        details = self.map_details(self.get_data("movie/%s"%tvshow_id,params),"tvshow")
        return details
    
    def get_movie_details_by_imdbid(self,imdb_id):
        '''get all moviedetails by providing imdbid'''
        tmdb_id = self.get_tmdbid_by_imdbid(imdb_id)
        return self.get_movie_details(tmdb_id) if tmdb_id else {}
        
    def get_tvshow_details_by_imdbid(self,imdb_id):
        '''get all tvshowdetails by providing imdbid'''
        tmdb_id = self.get_tmdbid_by_imdbid(imdb_id)
        return self.get_tvshow_details(tmdb_id) if tmdb_id else {}
        
    def get_tvshow_details_by_tvdbid(self,tvdb_id):
        '''get all tvshowdetails by providing imdbid'''
        tmdb_id = self.get_tmdbid_by_tvdbid(tvdb_id)
        return self.get_tvshow_details(tmdb_id) if tmdb_id else {}
    
    def get_tmdbid_by_imdbid(self,imdb_id):
        '''
            get tmdb_id for movie with given imdbid
        '''
        params = {"external_source": "imdb_id", "language": KODI_LANGUAGE}
        results = self.get_data("find/%s" %imdb_id,params)["movie_results"]
        return results[0]["id"] if results else None
        
    def get_tmdbid_by_tvdbid(self,tvdb_id):
        '''
            get tmdb_id for tvshow with given tvdbid
        '''
        results = self.get_data("find/%s" %tvdb_id,params)["tv_results"]
        return results[0]["id"] if results else None
    
    @staticmethod
    @rate_limiter(1)
    def get_data(endpoint, params):
        '''helper method to get data from tmdb json API'''
        params["api_key"] = "ae06df54334aa653354e9a010f4b81cb"
        url = u'http://api.themoviedb.org/3/%s'%endpoint
        return get_json(url,params)

    def map_details(self, data,media_type):
        '''helper method to map the details received from tmdb to kodi-json compatible formatting'''
        if not data:
            return {}
        details = {}
        details["tmdb_id"] = data["id"]
        details["originaltitle"] = data["original_title"]
        details["rating"] = data["vote_average"]
        details["votes"] = data["vote_count"]
        details["popularity"] = data["popularity"]
        details["plot"] = data["overview"]
        details["genre"] = [item["name"] for item in data["genres"]]
        details["homepage"] = data["homepage"]
        details["status"] = data["status"]
        details["cast"] = []
        details["castandrole"] = []
        details["writer"] = []
        details["director"] = []
        #cast
        for cast_member in data["credits"]["cast"]:
            cast_thumb = ""
            if cast_member["profile_path"]: 
                cast_thumb = "http://image.tmdb.org/t/p/original%s" %cast_member["profile_path"]
            details["cast"].append( {"name": cast_member["name"], "role": cast_member["character"], 
                "thumbnail": cast_member } )
            details["castandrole"].append( (cast_member["name"], cast_member["character"]) )
        #crew (including writers and directors)
        for crew_member in data["credits"]["crew"]:
            cast_thumb = ""
            if cast_member["profile_path"]: 
                cast_thumb = "http://image.tmdb.org/t/p/original%s" %cast_member["profile_path"]
            if crew_member["job"] in ["Author","Writer"]: 
                details["writer"] += crew_member["name"]
            if crew_member["job"] in ["Producer","Executive Producer"]: 
                details["director"] += crew_member["name"]
            if crew_member["job"] in ["Producer","Executive Producer","Author","Writer"]: 
                details["cast"].append( {"name": crew_member["name"], "role": crew_member["job"], 
                    "thumbnail": cast_member } ) 
        #artwork
        details["art"] = {}
        fanarts = self.get_best_images( data["images"]["backdrops"] )
        posters = self.get_best_images( data["images"]["posters"] )
        details["art"]["fanarts"] = fanarts
        details["art"]["posters"] = posters
        details["art"]["fanart"] = fanarts[0] if fanarts else ""
        details["art"]["poster"] = fanarts[0] if fanarts else ""
        #movies only
        if media_type == "movie":
            details["title"] = data["title"]
            if data["belongs_to_collection"]:
                details["set"] = data["belongs_to_collection"].get("name","")
            details["premiered"] = data["release_date"]
            details["year"] = int(data["release_date"].split("-")[0])
            details["tagline"] = data["tagline"]
            details["runtime"] = data["runtime"]
            details["imdbnumber"] = data["imdb_id"]
            details["budget"] = data["budget"]
            details["revenue"] = data["revenue"]
            details["studio"] = [item["name"] for item in data["production_companies"]]
            details["country"] = [item["name"] for item in data["production_countries"]]
            details["tag"] = [item["name"] for item in data["keywords"]["keywords"]]
        #tvshows only
        if media_type == "tvshow":
            details["title"] = data["name"] if data.data.get("name") else data["title"]
            details["director"] += [item["name"] for item in data["created_by"]]
            details["runtime"] = data["episode_run_time"][0] if data["episode_run_time"] else 0
            details["premiered"] = data["first_air_date"]
            details["year"] = int(data["first_air_date"].split("-")[0])
            details["lastaired"] = data["last_air_date"]
            details["studio"] = [item["name"] for item in data["networks"]]
            details["country"] = [item["name"] for item in data["origin_country"]]
            details["imdbnumber"] = data["external_ids"]["imdb_id"]
            details["tvdb_id"] = data["external_ids"]["tvdb_id"]
            details["tag"] = [item["name"] for item in data["keywords"]["results"]]
        #trailer
        for video in data["videos"]["results"]:
            if video["site"] == "YouTube" and video["type"] == "Trailer":
                details["trailer"] = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %video["key"]
                break
        return details

    @staticmethod
    def get_best_images(images):
        '''get the best 5 images based on number of likes and the language'''
        for image in images:
            score = 0
            score += image["vote_count"]
            score += image["vote_average"] * 10
            score += image["height"]
            if "iso_639_1" in image:
                if image["iso_639_1"] == KODI_LANGUAGE:
                    score += 1000
            image["score"] = score
            image["file_path"] = "http://image.tmdb.org/t/p/original%s" %image["file_path"]
        images = sorted(images,key=itemgetter("score"),reverse=True)[:5]
        return [image["file_path"] for image in images]
            
    @staticmethod
    def select_best_match(results,manual_select=False):
        '''helper to select best match or let the user manually select the best result from the search'''
        details = {}
        if results and manual_select:
            #show selectdialog to manually select the item
            results_list = []
            for item in self.get_data(search_query):
                label = item["name"] if "name" in item else item["title"]
                year = data["premiered"].split("-")[0] if "premiered" in item else data["release_date"].split("-")[0]
                label = "%s (%s)" %(label,year)
                listitem = xbmcgui.ListItem(label=label,iconImage="http://image.tmdb.org/t/p/original%s"%item["poster_path"])
                results_list.append(listitem)
            if manual_select and results_list:
                w = DialogSelect( "DialogSelect.xml", "", listing=results_list, window_title="%s - TMDB"%xbmc.getLocalizedString(283) )
                w.doModal()
                selected_item = w.result
                if selected_item != -1:
                    details = results[selected_item]
        elif results:
            #just grab the first item as best match
            details = results[0]
        return details