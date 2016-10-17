#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import *
import BeautifulSoup
import simplecache
import xbmcvfs

class GoogleImages(object):
    '''get images from google images'''
    
    def search_images(self,search_query):
        '''search google images with the given query, returns list of all images found'''
        return self.get_data(search_query)
        
    def search_image(self,search_query, manual_select=False):
        '''
            search google images with the given query, returns first/best match
            optional parameter: manual_select (bool), will show selectdialog to allow manual select by user
        '''
        image = ""
        images_list = []
        for img in self.get_data(search_query):
            if not manual_select and xbmcvfs.exists(img):
                #just return the first image found (assuming that will be the best match)
                return img
            else:
                #manual lookup, list results and let user pick one
                listitem = xbmcgui.ListItem(label=img,iconImage=img)
                images_list.append(listitem)
        if manual_select and images_list:
            w = DialogSelect( "DialogSelect.xml", "", listing=images_list, window_title="%s - Google"%xbmc.getLocalizedString(283) )
            w.doModal()
            selectedItem = w.result
            if selectedItem != -1:
                selectedItem = imagesList[selectedItem]
                image = selectedItem.getLabel()
        return image
        
    @staticmethod
    def get_data(search_query):
        '''helper method to get data from google images by scraping and parsing'''
        
        #get the items from cache first
        cache_str = u"SkinHelper.GoogleImages.%s"%search_query
        cache = simplecache.get(cache_str)
        if cache:
            return cache
        
        #no cache - get results from google images
        params = {"site":"imghp", "tbm":"isch", "tbs":"isz:l", "q":search_query}
        headers = {'User-agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows Phone OS 7.0; Trident/3.1; \
            IEMobile/7.0; LG; GW910)'}
        html = ''
        try:
            html = requests.get('https://www.google.com/search', headers=headers, params=params, timeout=5).text
        except Exception as e:
            log_msg("Error in GoogleImages.get_data: %s" %e,xbmc.LOGWARNING)
        soup = BeautifulSoup.BeautifulSoup(html)
        results = []
        for div in soup.findAll('div'):
            if div.get("id") == "images":
                for a in div.findAll("a"):
                    page = a.get("href")
                    try:
                        img = page.split("imgurl=")[-1]
                        img = img.split("&imgrefurl=")[0]
                        results.append( img )
                    except Exception: 
                        pass
        simplecache.set(cache_str,results)
        return results