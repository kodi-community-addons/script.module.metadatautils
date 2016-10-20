#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_json, rate_limiter
from kodidb import KodiDb
import xbmc, xbmcvfs

class ChannelLogos(object):
    '''get channellogo'''
    
    def __init__(self, *args):
        self.kodidb = KodiDb()
    
    def get_channellogo(self,channelname):
        '''get channellogo for the supplied channelname'''
        result = {}
        for searchmethod in [self.search_kodi,self.search_logosdb]:
            if result:
                break
            result["ChannelLogo"] = searchmethod(channelname)
        return result
        
    @staticmethod
    def search_logosdb(searchphrase):
        result = ""
        for searchphrase in [searchphrase, searchphrase.lower().replace(" hd","")]:
            if result: 
                break
            for item in self.get_data_from_logosdb(searchphrase):
                img = item['strLogoWide']
                if img and ".jpg" or ".png" in img:
                    result = img
                    break
        return result
        
    def search_kodi(self, searchphrase):
        '''search kodi json api for channel logo'''
        result = ""
        if xbmc.getCondVisibility("PVR.HasTVChannels"):
            results = self.kodidb.get_json('PVR.GetChannels',fields=[ "thumbnail" ],returntype="tvchannels", optparam=("channelgroupid", "alltv") )
            for item in results:
                if item["label"] == searchphrase:
                    channelicon = item['thumbnail']
                    if channelicon and xbmcvfs.exists(channelicon):
                        result = channelicon
                        break
        return result
    
    @staticmethod
    @rate_limiter(500)
    def get_data_from_logosdb(searchphrase):
        '''helper method to get data from thelogodb json API'''
        params = {"s": searchphrase}
        data = get_json('http://www.thelogodb.com/api/json/v1/3241/tvchannel.php',params)
        if data and data.get('channels'):
            return data["channels"]
        else:
            return []

    