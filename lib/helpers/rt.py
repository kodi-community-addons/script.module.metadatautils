#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    rt.py
    Get metadata from rt
"""

import os, sys
from .utils import get_json, requests, try_parse_int, log_msg
import bs4 as BeautifulSoup
from simplecache import use_cache
import json

class Rt(object):
    """Info from rt (currently only top250)"""

    def __init__(self, simplecache=None, kodidb=None):
        """Initialize - optionaly provide simplecache object"""
        if not simplecache:
            from simplecache import SimpleCache
            self.cache = SimpleCache()
        else:
            self.cache = simplecache
        if not kodidb:
            if sys.version_info.major == 3:
                from .kodidb import KodiDb
            else:
                from kodidb import KodiDb
            self.kodidb = KodiDb()
        else:
            self.kodidb = kodidb

    @use_cache(2)
    def get_details_tv_rt(self, title):
        """get rt details by providing an tvshowtitle"""
        params = {"q": title, "t": "tvseries", "limit": "1"}
        data = self.get_data(params)
        #log_msg("get_RT_all - data from json %s -%s" %  (title, data))
        return self.map_tv_details(data) if data else None

    def get_details_movie_rt(self, title):
        """get rt details by providing an tvshowtitle"""
        params = {"q": title, "t": "movie", "limit": "1"}
        data = self.get_data(params)
        result = {}
        for key, value in data.items():
            if data and data.get("movies"):
                 for item in data["movies"]:
                    result["title"] = item["url"].split("/m/")[1]
                    title = result["title"]
                    html = ''
                    page = []
                    html = requests.get("https://www.rottentomatoes.com/m/%s" %
                            title, timeout=15).text
                    #log_msg("get_RT_all - html from json %s -%s" %  (title, html))
                    soup = BeautifulSoup.BeautifulSoup(html, features="html.parser")
                    for div in soup.findAll('div', id="rating-root"):
                        page = div.get("data-movie-id")
                    url = requests.get('https://api.flixster.com/android/api/v2/movies/%s.json' % page, timeout=15)
                    data = json.loads(url.text)
        return self.map_details(data) if data else None
 
    def get_ratings_movie_rt(self, title):
        """get rt details by providing an tvshowtitle"""
        params = {"q": title, "t": "movie", "limit": "1"}
        data = self.get_data(params)
        result = {}
        for key, value in data.items():
            if data and data.get("movies"):
                 for item in data["movies"]:
                    result["title"] = item["url"].split("/m/")[1]
                    title = result["title"]
                    headers = {'User-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows Phone OS 7.0; Trident/3.1; \
                                IEMobile/7.0; LG; GW910)'}
                    html = ''
                    page = []
                    html = requests.get("https://www.rottentomatoes.com/m/%s" %
                            title, headers=headers, timeout=5).text
                    soup = BeautifulSoup.BeautifulSoup(html, features="html.parser")
                    for div in soup.find_all("script", type="application/json"):
                        for a_link in div:
                            data = json.loads(a_link)
                            if data and data.get("modal"):
                                data = data["modal"]
                                if data and data.get("audienceScoreAll"):
                                    if data["audienceScoreAll"].get("averageRating"):
                                        result["audienceScoreAll.averageRating"] = data["audienceScoreAll"].get("averageRating")
                                    if data["audienceScoreAll"].get("likedCount"):
                                        result["audienceScoreAll.likedCount"] = data["audienceScoreAll"].get("likedCount")
                                    if data["audienceScoreAll"].get("notLikedCount"):
                                        result["audienceScoreAll.notLikedCount"] = data["audienceScoreAll"].get("notLikedCount")
                                    if data["audienceScoreAll"].get("ratingCount"):
                                        result["audienceScoreAll.ratingCount"] = data["audienceScoreAll"].get("ratingCount") 
                                    if data["audienceScoreAll"].get("reviewCount"):
                                        result["audienceScoreAll.reviewCount"] = data["audienceScoreAll"].get("reviewCount")
                                    if data["audienceScoreAll"].get("audienceClass"):
                                        result["audienceScoreAll.audienceClass"] = data["audienceScoreAll"].get("audienceClass") 
                                    if data["audienceScoreAll"].get("score"):
                                        result["audienceScoreAll.score"] = data["audienceScoreAll"].get("score")
                                if data and data.get("tomatometerScoreAll"):
                                    if data["tomatometerScoreAll"].get("averageRating"):
                                        result["tomatometerScoreAll.averageRating"] = data["tomatometerScoreAll"].get("averageRating")
                                    if data["tomatometerScoreAll"].get("likedCount"):
                                        result["tomatometerScoreAll.likedCount"] = data["tomatometerScoreAll"].get("likedCount")
                                    if data["tomatometerScoreAll"].get("notLikedCount"):
                                        result["tomatometerScoreAll.notLikedCount"] = data["tomatometerScoreAll"].get("notLikedCount")
                                    if data["tomatometerScoreAll"].get("ratingCount"):
                                        result["tomatometerScoreAll.ratingCount"] = data["tomatometerScoreAll"].get("ratingCount") 
                                    if data["tomatometerScoreAll"].get("reviewCount"):
                                        result["tomatometerScoreAll.reviewCount"] = data["tomatometerScoreAll"].get("reviewCount")
                                    if data["tomatometerScoreAll"].get("tomatometerState"):
                                        result["tomatometerScoreAll.tomatometerState"] = data["tomatometerScoreAll"].get("tomatometerState") 
                                    if data["tomatometerScoreAll"].get("score"):
                                        result["tomatometerScoreAll.score"] = data["tomatometerScoreAll"].get("score")
                                if data and data.get("tomatometerScoreTop"):
                                    if data["tomatometerScoreTop"].get("averageRating"):
                                        result["tomatometerScoreTop.averageRating"] = data["tomatometerScoreTop"].get("averageRating")
                                    if data["tomatometerScoreTop"].get("likedCount"):
                                        result["tomatometerScoreTop.likedCount"] = data["tomatometerScoreTop"].get("likedCount")
                                    if data["tomatometerScoreTop"].get("notLikedCount"):
                                        result["tomatometerScoreTop.notLikedCount"] = data["tomatometerScoreTop"].get("notLikedCount")
                                    if data["tomatometerScoreTop"].get("ratingCount"):
                                        result["tomatometerScoreTop.ratingCount"] = data["tomatometerScoreTop"].get("ratingCount") 
                                    if data["tomatometerScoreTop"].get("reviewCount"):
                                        result["tomatometerScoreTop.reviewCount"] = data["tomatometerScoreTop"].get("reviewCount")
                                    if data["tomatometerScoreTop"].get("tomatometerState"):
                                        result["tomatometerScoreTop.tomatometerState"] = data["tomatometerScoreTop"].get("tomatometerState") 
                                    if data["tomatometerScoreTop"].get("score"):
                                        result["tomatometerScoreTop.score"] = data["tomatometerScoreTop"].get("score")
        return result
        
    def get_data(self, params):
        """helper method to get data from rt  API"""
        base_url = 'https://www.rottentomatoes.com/api/private/v2.0/search?'
        return get_json(base_url, params)
     
    def map_tv_details(self, data):
        """helper method to map the details received from rt to kodi compatible format"""
        result = {}
        if sys.version_info.major == 3:
            for key, value in data.items():
                if data and data.get("tvSeries"):
                    for item in data["tvSeries"]:
                        if item["title"]:
                            result["title"] = item["title"]
                        if item["startYear"]:
                            result["startYear"] = item["startYear"]
                        if item["endYear"]:
                            result["endYear"] = item["endYear"]
                        if item["meterClass"]:
                            result["tomatoImage"] = item["meterClass"]
                        if item["url"]:
                            result["url"] = item["url"]
                        try:
                            if item["meterScore"]:
                                result["RottenTomatoes.Meter"] = item["meterScore"]
                        except Exception:
                            pass
        return result

    def map_details(self, data):
        """helper method to map the details received from RT kodi compatible format"""
        result = {}
        if sys.version_info.major == 3:
            for key, value in data.items():
                # filter the N/A values
                if value in ["N/A", "None"] or not value:
                    continue
                if key == "id":
                    result["rt.id"] = value
                if key == "title":
                    result["rt.title"] = value
                if key == "mpaa":
                    result["rt.mpaa"] = value
                if key == "synopsis":
                    result["synopsis"] = value
                if key == "country":
                    result["country"] = value
                if key == "runningTime":
                    result["running.time"] = value
                if data.get("videos"):
                    trailer_videos = []
                    for count, item in enumerate(data["videos"]):
                        trailer_videos.append(item["videoUrl"])
                        result["rt.title.%s.trailer" % count] = item["title"]
                        result["rt.image.%s.trailer" % count] = item["imageUrl"]
                        result["rt.video.%s.trailer" % count] = item["videoUrl"]
                        result["rt.duration.%s.trailer" % count] = item["duration"]
                if data.get("theaterReleaseDate"):
                    if data["theaterReleaseDate"].get("year"):
                        result["rt.year"] = data["theaterReleaseDate"].get("year")
                    if data["theaterReleaseDate"].get("month"):
                        result["rt.month"] = data["theaterReleaseDate"].get("month")
                    if data["theaterReleaseDate"].get("day"):
                        result["rt.day"] = data["theaterReleaseDate"].get("day")
                if data.get("poster"):
                    if data["poster"].get("original"):
                        result["art.rt.poster"] = data["poster"].get("original")
                if data.get("trailer"):
                    if data["trailer"].get("hd"):
                        result["rt.trailer"] = data["trailer"].get("hd")
                if data and data.get("reviews"):
                    data = data["reviews"]
                    if data.get("criticsNumReviews"):
                        result["rt.criticsNumReviews"] = data.get("criticsNumReviews")
                    if data.get("flixster") and data["flixster"].get("average"):
                        result["flixster.average"] = round(data["flixster"].get("average"), 2)
                    if data.get("flixster") and data["flixster"].get("numNotInterested"):
                        result["flixster.numNotInterested"] = data["flixster"].get("numNotInterested")
                    if data.get("flixster") and data["flixster"].get("likeability"):
                        result["flixster.likeability"] = data["flixster"].get("likeability")
                    if data.get("flixster") and data["flixster"].get("numScores"):
                        result["flixster.numScores"] = data["flixster"].get("numScores")
                    if data.get("flixster") and data["flixster"].get("numWantToSee"):
                        result["flixster.numWantToSee"] = data["flixster"].get("numWantToSee")
                    if data.get("flixster") and data["flixster"].get("popcornScore"):
                        result["flixster.popcornScore"] = data["flixster"].get("popcornScore")
                    if data.get("rottenTomatoes") and data["rottenTomatoes"].get("rating"):
                        result["rt.rating"] = data["rottenTomatoes"].get("rating")
                    if data.get("rottenTomatoes") and data["rottenTomatoes"].get("certifiedFresh"):
                        result["rt.certifiedFresh"] = data["rottenTomatoes"].get("certifiedFresh")
                    if data.get("rottenTomatoes") and data["rottenTomatoes"].get("consensus"):
                        result["rt.consensus"] = data["rottenTomatoes"].get("consensus")
                    if data["critics"]:
                        critics_review = []
                        for count, item in enumerate(data["critics"]):
                            critics_review.append(item["id"])
                            result["rt.review.%s.id" % count] = item["id"]
                            result["rt.review.%s.name" % count] = item["name"]
                            result["rt.review.%s.rating" % count] = item["rating"]
                            result["rt.review.%s.review" % count] = item["review"]
                    if data["recent"]:
                        critics_recent = []
                        for count, item in enumerate(data["recent"]):
                            critics_recent.append(item["id"])
                            if item.get("score"):
                                result["rt.recent.%s.score" % count] = item["score"]
                            if item.get("review"):
                                result["rt.recent.%s.review" % count] = item["review"]
                            if item and item.get("user"):
                                item = item["user"]
                                if item.get("userName"):
                                    result["rt.recent.%s.userName" % count] = item["userName"]
                                if item.get("firstName"):
                                    result["rt.recent.%s.firstName" % count] = item["firstName"]
                                if item.get("lastName"):
                                    result["rt.recent.%s.lastName" % count] = item["lastName"]
                                if item.get("score"):
                                    result["rt.recent.%s.score" % count] = item["score"]
                                if item and item.get("images"):
                                    item = item["images"]
                                    if item.get("thumbnail"):
                                        result["rt.recent.%s.thumbnail" % count] = item["thumbnail"]
        return result