#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import log_msg, get_json, KODI_LANGUAGE
from operator import itemgetter

class Tmdb(object):
    '''get artwork from fanart.tv'''

    def search_multi(self,title,year=""):
        '''
            Search tmdb for a specific entry (can be movie or tvshow), parameters:
            title: (required) the title of the movie/tvshow to search for
            year: (optional) the year of the media to search for (enhances search result if supplied)
        '''
        params = {"query": title, "language": KODI_LANGUAGE}
        data = self.get_data("search/multi",params)
        if data and year:
            #prefer result with correct year
            newdata = []
            for item in data:
                if item.get("first_air_date") and year in item["first_air_date"]:
                    newdata.append(item)
                elif item.get("release_date") and year in item["release_date"]:
                    newdata.append(item)
            if newdata:
                return newdata
            else:
                return data

    def search_movie(self,title,year=""):
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

    def search_tv(self,title,year=""):
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

    def search_person(self,name):
        '''
            Search tmdb for a specific actor/person, returns a list of all closest matches
            required parameter: name --> the name of the person
        '''
        params = {"query": name, "language": KODI_LANGUAGE}
        return self.get_data("search/person",params)

    def get_movie_details(self,movie_id):
        '''get all moviedetails'''
        params = {
            "append_to_response": "credits,images&include_image_language=%s,en"%KODI_LANGUAGE, 
            "language": KODI_LANGUAGE
            }
        return self.get_data("movie/%s"%movie_id,params)
        
        
        url = 'http://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=videos' %(tvdbid,tmdb_apiKey,language)
                        if includeCast: url += ',credits'

    @staticmethod
    def get_data(endpoint, params):
        '''helper method to get data from tmdb json API'''
        params["api_key"] = "ae06df54334aa653354e9a010f4b81cb"
        url = u'http://api.themoviedb.org/3/%s'%endpoint
        return get_json(url,params)

    @staticmethod
    def map_details(data,media_type):
        '''helper method to map the details received from tmdb to kodi compatible formatting'''
        details = {}
        details["title"] = data["title"]
        details["originaltitle"] = data["original_title"]
        details["rating"] = data["vote_average"]
        details["votes"] = data["vote_count"]
        details["plot"] = data["overview"]

        #movies only
        if media_type == "movie":
            details["set"] = data["belongs_to_collection"].get("name","")
            details["releasedate"] = data["release_date"]
            details["year"] = data["release_date"].split("-")[0]
            details["tagline"] = data["tagline"]
            details["tagline"] = data["tagline"]
        
        
        
        

        return artwork

    @staticmethod
    def score_image(item):
        '''score item based on number of likes and the language'''
        score = 0
        score += item["likes"]
        if "lang" in item:
            if item["lang"] == KODI_LANGUAGE:
                score += 1000
            elif item["lang"] == "en":
                score += 500
        item["score"] = score
        return item
