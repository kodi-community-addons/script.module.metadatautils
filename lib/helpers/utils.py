#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmc
import os,sys
from traceback import format_exc
from datetime import datetime, timedelta
import time
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import urllib, urlparse

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
KODI_LANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)

#setup requests with some additional options
requests.packages.urllib3.disable_warnings()
s = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[ 500, 502, 503, 504 ])
s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))

def log_msg(msg, loglevel = xbmc.LOGNOTICE):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper ArtUtils --> %s" %msg, level=loglevel)

def log_exception(modulename, exceptiondetails):
    log_msg(format_exc(sys.exc_info()),xbmc.LOGWARNING)
    log_msg("ERROR in %s ! --> %s" %(modulename,exceptiondetails), xbmc.LOGERROR)

def get_json(url, params=None ,rate_limiter=True):
    '''get info from a rest api - protect webserver (and api keys!) by applying a rate limiter'''
    
    #very basic rate limiter to make sure a domain is only hit once at the same time
    win = xbmcgui.Window(10000)
    limit_str = "rate_limit.%s" %urlparse.urlparse(url).hostname
    count = 0
    #if url already active (rate limited), we'll have to wait
    while rate_limiter and win.getProperty(limit_str) and count < 100:
        xbmc.sleep(50)
        log_msg("Rate limiter active for %s"%limit_str, xbmc.LOGWARNING)
        count += 1
    result = None
    if not params:
        params = {}
    try:
        #mark url as active in the rate limit win prop while our request is busy
        win.setProperty(limit_str,"active")
        response = requests.get(url,params=params, timeout=15)
        if response and response.content and response.status_code == 200:
            result = json.loads(response.content.decode('utf-8','replace'))
            if "results" in result:
                result = result["results"]
            elif "result" in result:
                result = result["result"]
    except Exception as e:
        log_msg("get_json failed for url: %s -- exception: %s" %(url,e))
    #mark url as free again and return the results
    win.clearProperty(limit_str)
    del win
    return result

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

def try_parse_int(string):
    try:
        return int(string)
    except Exception:
        return 0

def extend_dict(org_dict, new_dict, allow_overwrite=None):
    '''Create a new dictionary with a's properties extended by b,
    without overwriting existing values.'''
    if not new_dict:
        return org_dict
    for key, value in new_dict.iteritems():
        if value:
            if not org_dict.get(key):
                #orginal dict doesn't has this key (or no value), just overwrite
                org_dict[key] = value
            else:
                #original dict already has this key, append results
                if isinstance(value, list):
                    #make sure that our original value also is a list
                    if isinstance(org_dict[key], list):
                        for item in value:
                            if not item in org_dict[key]:
                                org_dict[key].append(item)
                    else:
                        log_msg("extend_dict: type mismatch! key: %s - newvalue: %s  -  existing value: %s" 
                            %(key, value, org_dict[key]))
                elif isinstance(value, dict):
                    org_dict[key] = extend_dict(org_dict[key], value)
                elif allow_overwrite and key in allow_overwrite:
                    log_msg("extend_dict: key %s overwriting existing value in dict - orgvalue: %s - newvalue: %s" 
                        %(key,org_dict[key],value))
                    org_dict[key] = value
                else:
                    log_msg("extend_dict: key %s already has value in dict - orgvalue: %s - newvalue: %s" 
                        %(key,org_dict[key],value))
    return org_dict

def get_local_date_from_utc(timestring):
    try:
        systemtime = xbmc.getInfoLabel("System.Time")
        utc = datetime.fromtimestamp(time.mktime(time.strptime(timestring, '%Y-%m-%d %H:%M:%S')))
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp(epoch)
        correcttime = utc + offset
        if "AM" in systemtime or "PM" in systemtime:
            return (correcttime.strftime("%Y-%m-%d"),correcttime.strftime("%I:%M %p"))
        else:
            return (correcttime.strftime("%d-%m-%Y"),correcttime.strftime("%H:%M"))
    except Exception as e:
        log_exception(__name__,e)
        return (timestring,timestring)
        

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
