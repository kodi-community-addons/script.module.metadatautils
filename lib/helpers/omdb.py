#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, formatted_number, rate_limiter, log_msg, int_with_commas
import datetime

class Omdb(object):
    '''get metadata from omdb'''
    
    def __init__(self, *args):
        pass
    
    def get_details_by_imdbid(self,imdb_id):
        '''get omdb details by providing an imdb id'''
        params = {"i": imdb_id}
        data = self.get_data(params)
        return self.map_details(data)
    
    def get_details_by_title(self,title,year="",media_type=""):
        ''' get omdb details by title
            title --> The title of the media to look for (required)
            year (str/int)--> The year of the media (optional, better results of provided)
            media_type --> The type of the media: movie/tvshow (optional, better results of provided)
        '''
        if "movie" in media_type:
            media_type = "movie"
        if "show" in media_type:
            media_type = "series"
        params = {"t": title, "y": year, "type": media_type}
        data = self.get_data(params)
        return self.map_details(data)
        
    @staticmethod
    @rate_limiter(250)
    def get_data(params):
        '''helper method to get data from omdb json API'''
        params["plot"] = "short"
        params["tomatoes"] = True
        params["r"] = "json"
        data = get_json('http://www.omdbapi.com/',params)
        if data:
            return data
        else:
            return {}

    @staticmethod
    def map_details(data):
        '''helper method to map the details received from omdb to kodi compatible format'''
        result = {}
        for key, value in data.iteritems():
            #filter the N/A values
            if value == "N/A" or not value:
                continue
            if key == "Title":
                result["title"] = value
            elif key == "Year": 
                result["year"] = int(value.split("-")[0])
            if key == "Rated":
                result["mpaa"] = value
            elif key == "Title":
                result["title"] = value
            elif key == "Released":
                result["premiered"] = datetime.datetime.strptime(value,"%d %b %Y").strftime('%Y-%m-%d')
                result["premiered.formatted"] = value
            elif key == "Runtime":
                result["runtime"] = int(value.replace(" min",""))
            elif key == "Genre":
                result["genre"] = value.split(", ")
            elif key == "Director":
                result["director"] = value.split(", ")
            elif key == "Writer":
                result["writer"] = value.split(", ")
            elif key == "Country":
                result["country"] = value.split(", ")
            elif key == "Awards": 
                result["awards"] = value
                result["SkinHelper.RottenTomatoesAwards"] = value#legacy
            elif key == "Poster": 
                result["thumb"] = value
            elif key == "Metascore": 
                result["metacritic.rating"] = value
                result["SkinHelper.metacritic.rating"] = value#legacy
            elif key == "imdbRating":
                result["imdb.rating"] = value
                result["rating"] = float(value)
                result["imdb.rating.percent"] = "%s" %(int(float(value) * 10))
                result["SkinHelper.imdb.rating"] = value#legacy
            elif key == "imdbVotes": 
                result["imdb.votes"] = value
                result["votes"] = int(value.replace(",",""))
            elif key == "imdbID": 
                result["imdbnumber"] = value
            elif key == "BoxOffice": 
                result["boxoffice"] = value
            elif key == "DVD": 
                result["dvdrelease"] = datetime.datetime.strptime(value,"%d %b %Y").strftime('%Y-%m-%d')
                result["dvdrelease.formatted"] = value
            elif key == "Production": 
                result["studio"] = value.split(", ")
            elif key == "Website": 
                result["homepage"] = value
            #rotten tomatoes
            elif key == "tomatoMeter": 
                result["rottentomatoes.meter"] = value
                result["rottentomatoesmeter"] = value
            if key == "tomatoRating": 
                result["rottentomatoes.rating"] = value
                result["rottentomatoes.rating.percent"] = "%s" %(int(float(value) * 10))
                result["SkinHelper.rottentomatoesrating"] = value #legacy
                result["SkinHelper.rottentomatoesrating.percent"] = "%s" %(int(float(value) * 10))#legacy
            elif key == "tomatoFresh": 
                result["rottentomatoes.fresh"] = value
                result["SkinHelper.rottentomatoesfresh"] = value#legacy
            elif key == "tomatoReviews": 
                result["rottentomatoes.reviews"] = formatted_number(value)
                result["SkinHelper.rottentomatoesreviews"] = formatted_number(value)#legacy
            elif key == "tomatoRotten": 
                result["rottentomatoes.rotten"] = value
                result["SkinHelper.rottentomatoesrotten"] = value#legacy
            elif key == "tomatoImage": 
                result["rottentomatoes.image"] = value
                result["SkinHelper.rottentomatoesimage"] = value#legacy
            elif key == "tomatoConsensus": 
                result["rottentomatoes.consensus"] = value
                result["SkinHelper.rottentomatoesconsensus"] = value#legacy
            elif key == "tomatoUserMeter": 
                result["rottentomatoes.usermeter"] = value
                result["SkinHelper.rottentomatoesaudiencemeter"] = value#legacy
            elif key == "tomatoUserRating": 
                result["rottentomatoes.userrating"] = value
                result["rottentomatoes.userrating.percent"] = "%s" %(int(float(value) * 10))
                result["SkinHelper.rottentomatoesaudiencerating"] = value#legacy
                result["SkinHelper.rottentomatoesaudiencerating.percent"] = "%s" %(int(float(value) * 10))#legacy
            elif key == "tomatoUserReviews": 
                result["rottentomatoes.userreviews"] = int_with_commas(value)
                result["SkinHelper.rottentomatoesaudiencereviews"] = int_with_commas(value)#legacy
            elif key == "tomatoURL": 
                result["rottentomatoes.url"] = value
        return result
        