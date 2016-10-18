#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmc, xbmcaddon
import os,sys
from traceback import format_exc
from datetime import datetime, timedelta
import time
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from simplecache import SimpleCache


simplecache = SimpleCache()

try:
    from multiprocessing.pool import ThreadPool as Pool
    supportsPool = True
except Exception: 
    supportsPool = False

try:
    import simplejson as json
except Exception:
    import json

ADDON_ID = "script.module.skin.helper.artutils"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_NAME = ADDON.getAddonInfo('name').decode("utf-8")
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
ADDON_VERSION = ADDON.getAddonInfo('version').decode("utf-8")
WINDOW = xbmcgui.Window(10000)
SETTING = ADDON.getSetting
KODI_LANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)

requests.packages.urllib3.disable_warnings()
s = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))

def log_msg(msg, loglevel = xbmc.LOGNOTICE):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper ArtUtils --> %s" %msg, level=loglevel)

def log_exception(modulename, exceptiondetails):
    log_msg(format_exc(sys.exc_info()),xbmc.LOGWARNING)
    log_msg("ERROR in %s ! --> %s" %(modulename,exceptiondetails), xbmc.LOGERROR)
    
def get_json(url,params=None,cache_days=14):
    '''get info from a rest api'''
    result = None
    if not params:
        params = {}
    #always try cache first, we don't want to overload the webservers with the same requests
    cache_str = "SkinHelper.ArtUtils.%s.%s" %(url,params)
    cache = simplecache.get(cache_str)
    if cache and cache_days:
        result = cache
    else:
        try:
            response = requests.get(url,params=params, timeout=15)
            if response and response.content and response.status_code == 200:
                result = json.loads(response.content.decode('utf-8','replace'))
                if "results" in result:
                    result = result["results"]
                if "result" in result:
                    result = result["result"]
                #store in cache for quick access later - TODO: what to do for not found responses ?
                if cache_days:
                    simplecache.set(cache_str,result,expiration=timedelta(days=cache_days))
        except Exception as e:
            log_msg("get_json failed for url: %s -- exception: %s" %(url,e))
    return result
  
def rate_limiter(milliseconds=500):
    '''very basic rate limiter'''
    def decorate(func):
        def func_wrapper(*args, **kwargs):
            self = args[0]
            limit_str = "rate_limit.%s.%s" %(self.__class__.__name__, func.__name__)
            for item in args:
                if not item == self:
                    limit_str += ".%s" %item
            for item in kwargs.itervalues():
                limit_str += ".%s" %item
            count = 0
            while WINDOW.getProperty(limit_str) and count < 20:
                xbmc.sleep(250)
                log_msg("Rate limiter active for %s"%limit_str, xbmc.LOGWARNING)
                count += 1
            WINDOW.setProperty(limit_str,"active")
            result = func(*args, **kwargs)
            xbmc.sleep(milliseconds)
            WINDOW.clearProperty(limit_str)
            return result
        return func_wrapper
    return decorate
 
def try_encode(text, encoding="utf-8"):
    try:
        return text.encode(encoding,"ignore")
    except Exception:
        return text

def try_decode(text, encoding="utf-8"):
    try:
        return text.decode(encoding,"ignore")
    except Exception:
        return text

def formatted_number(x):
    try:
        x = int(x)
        if x < 0:
            return '-' + formatted_number(-x)
        result = ''
        while x >= 1000:
            x, r = divmod(x, 1000)
            result = ",%03d%s" % (r, result)
        return "%d%s" % (x, result)
    except Exception: 
        return ""
        
def process_method_on_list(method_to_run,items):
    '''helper method that processes a method on each listitem with pooling if the system supports it'''
    all_items = []
    if supportsPool:
        pool = Pool()
        try:
            all_items = pool.map(method_to_run, items)
        except Exception:
            #catch exception to prevent threadpool running forever
            log_msg(format_exc(sys.exc_info()))
            log_msg("Error in %s" %method_to_run)
        pool.close()
        pool.join()
    else:
        all_items = [method_to_run(item) for item in items]
    all_items = filter(None, all_items)
    return all_items

def get_clean_image(image):
    if image and "image://" in image:
        image = image.replace("image://","").replace("music@","")
        image=urllib.unquote(image.encode("utf-8"))
        if image.endswith("/"):
            image = image[:-1]
    return try_decode(image)  
    
def get_duration_string(duration):
    if duration == None or duration == 0:
        return ""
    try:
        full_minutes = int(duration)
        minutes = str(full_minutes % 60)
        minutes = str(minutes).zfill(2)
        hours   = str(full_minutes // 60)
        formatted_time = hours + ':' + minutes
    except Exception as exc:
        log_exception(__name__,exc)
        return ""
    return ( hours, minutes, formatted_time )

def int_with_commas(x):
    try:
        x = int(x)
        if x < 0:
            return '-' + int_with_commas(-x)
        result = ''
        while x >= 1000:
            x, r = divmod(x, 1000)
            result = ",%03d%s" % (r, result)
        return "%d%s" % (x, result)
    except Exception: 
        return ""

       
class DialogSelect( xbmcgui.WindowXMLDialog ):
    '''wrapper around Kodi dialogselect to present a list of items'''
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.listing = kwargs.get( "listing" )
        self.window_title = kwargs.get( "window_title","" )
        self.result = -1

    def onInit(self):
        self.list_control = self.getControl(6)
        self.getControl(1).setLabel(self.window_title)
        self.getControl(3).setVisible(False)
        try:
            self.getControl(7).setLabel(xbmc.getLocalizedString(222))
        except Exception:
            pass

        self.getControl(5).setVisible(False)

        #add our items to the listing  and focus the control
        self.list_control.addItems( self.listing )
        self.setFocus(self.list_control)

    def onAction(self, action):
        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, control_id):
        if control_id in (6, 3,):
            num = self.list_control.getSelectedPosition()
            self.result = num
        else:
            self.result = -1
        self.close()
