#!/usr/bin/python
# -*- coding: utf-8 -*-

from simplecache import SimpleCache
import xbmc, xbmcvfs
import os
from datetime import timedelta

class StudioLogos():
    
    def __init__(self, *args):
        self.cache = SimpleCache()

    def get_studio_logo(self, studios, lookup_path):
        if not studios: 
            return {}
        result = {}
        if not isinstance(studios,list):
            studios = studios.split(" / ")
        result["Studio"] = studios[0]
        result['Studios'] = "[CR]".join(studios)
        result['StudioLogo'] = self.match_studio_logo(studios, self.get_studio_logos(lookup_path))
        return result

    def get_studio_logos(self, lookup_path):
        cache_str = u"SkinHelper.StudioLogos.%s"%lookup_path
        cache = self.cache.get( cache_str )
        if cache: 
            return cache
        #no cache - start lookup
        all_logos = {}
        if lookup_path.startswith("resource://"):
            all_logos = self.get_resource_addon_files(lookup_path)
        else:
            if not (lookup_path.endswith("/") or lookup_path.endswith("\\")):
                lookup_path = lookup_path + os.sep
                all_logos = self.list_files_in_path(lookup_path)
        #save in cache and return
        self.cache.set(cache_str,all_logos,expiration=timedelta(days=7))
        return all_logos

    @staticmethod
    def match_studio_logo(studios,studiologos):
        #try to find a matching studio logo
        studiologo = ""
        for studio in studios:
            if studiologo:
                break
            studio = studio.lower()
            #find logo normal
            if studiologos.has_key(studio):
                studiologo = studiologos[studio]
            if not studiologo:
                #find logo by substituting characters
                if " (" in studio:
                    studio = studio.split(" (")[0]
                    if studiologos.has_key(studio):
                        studiologo = studiologos[studio]
            if not studiologo:
                #find logo by substituting characters for pvr channels
                if " HD" in studio:
                    studio = studio.replace(" HD","")
                elif " " in studio:
                    studio = studio.replace(" ","")
                if studiologos.has_key(studio):
                    studiologo = studiologos[studio]
        return studiologo

    def get_resource_addon_files(self,resourcePath):
        # get listing of all files (eg studio logos) inside a resource image addonName
        # read data from our permanent cache file to prevent that we have to query the resource addon
        cache = self.cache.get(resourcePath)
        if cache: return cache
        #read resource addon as file listing
        data = self.list_files_in_path(resourcePath)
        # safe data to our permanent cache file, high timedelta because reading the resource addon list causes strange behaviour.
        self.cache.set(resourcePath,data,expiration=timedelta(days=90))
        return data

    def list_files_in_path( self, path):
        #used for easy matching of studio logos
        allFilesList = {}
        dirs, files = xbmcvfs.listdir(path)
        for file in files:
            file = file.decode("utf-8")
            name = file.split(".png")[0].lower()
            allFilesList[name] = path + file
        for dir in dirs:
            dirs2, files2 = xbmcvfs.listdir(os.path.join(path,dir)+os.sep)
            for file in files2:
                file = file.decode("utf-8")
                dir = dir.decode("utf-8")
                name = dir + "/" + file.split(".png")[0].lower()
                if "/" in path:
                    sep = "/"
                else:
                    sep = "\\"
                allFilesList[name] = path + dir + sep + file
        #return the list
        return allFilesList
