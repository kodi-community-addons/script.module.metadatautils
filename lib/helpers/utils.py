#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui, xbmc
import os,sys
from traceback import format_exc
import requests
import arrow
from datetime import timedelta
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import urllib, urlparse
import unicodedata
import re

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

def log_msg(msg, loglevel = xbmc.LOGDEBUG):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper ArtUtils --> %s" %msg, level=loglevel)

def log_exception(modulename, exceptiondetails):
    log_msg(format_exc(sys.exc_info()),xbmc.LOGWARNING)
    log_msg("ERROR in %s ! --> %s" %(modulename,exceptiondetails), xbmc.LOGERROR)

def get_json(url, params=None, retries=0):
    '''get info from a rest api'''
    result = {}
    if not params:
        params = {}
    try:
        response = requests.get(url,params=params, timeout=15)
        if response and response.content and response.status_code == 200:
            result = json.loads(response.content.decode('utf-8','replace'))
            if "results" in result:
                result = result["results"]
            elif "result" in result:
                result = result["result"]
            return result
    except Exception as e:
        if "Read timed out" in str(e) and not retries == 10:
            #auto retry...
            xbmc.sleep(500)
            log_msg("get_json time-out for url: %s -- auto retrying..." %(url))
            return get_json(url, params, retries+1)
        elif "getaddrinfo failed" in str(e):
            log_msg("No internet or server not reachable - request failed for url: %s" %url, xbmc.LOGWARNING)
            return None
        else:
            log_exception(__name__, e)
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
        
def urlencode(text):
   blah = urllib.urlencode({'blahblahblah':try_encode(text)})
   blah = blah[13:]
   return blah

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
        if not isinstance(image, unicode):
            image = image.decode("utf8")
    return image

def get_duration(duration):
    '''transform duration time in minutes to hours:minutes'''
    if not duration:
        return {}
    if isinstance(duration,(unicode,str)):
        duration.replace("min","").replace("","").replace(".","")
    try:
        total_minutes = int(duration)
        hours = total_minutes / 60
        minutes = total_minutes - (hours * 60)
        formatted_time = "%s:%s" %(hours, str(minutes).zfill(2))
    except Exception as exc:
        log_exception(__name__,exc)
        return {}
    return {
            "Duration": formatted_time, 
            "Duration.Hours": hours, 
            "Duration.Minutes": minutes,
            "Runtime": total_minutes,
            "RuntimeExtended": "%s %s" %(total_minutes,xbmc.getLocalizedString(12391)),
            "DurationAndRuntime": "%s (%s min.)" %(formatted_time, total_minutes),
            "DurationAndRuntimeExtended": "%s (%s %s)" %(formatted_time, total_minutes, xbmc.getLocalizedString(12391))
           }

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
                    #previous value was str, combine both in list
                    elif isinstance(org_dict[key], (str,unicode)):
                        org_dict[key] = [ org_dict[key] ]
                        for item in value:
                            if not item in org_dict[key]:
                                org_dict[key].append(item)
                elif isinstance(value, dict):
                    org_dict[key] = extend_dict(org_dict[key], value)
                elif allow_overwrite and key in allow_overwrite:
                    #value may be overwritten
                    org_dict[key] = value
                else:
                    #conflicht, leave alone
                    pass
    return org_dict
          
def localdate_from_utc_string(timestring):
    '''helper to convert internal utc time (used in pvr) to local timezone'''
    utc_datetime = arrow.get(timestring)
    local_datetime = utc_datetime.to('local')
    return local_datetime.format("YYYY-MM-DD HH:mm:ss")

def localized_date_time(timestring):
    '''returns localized version of the timestring (used in pvr)'''
    date_time = arrow.get(timestring)
    local_date = date_time.strftime(xbmc.getRegion("dateshort"))
    local_time = date_time.strftime(xbmc.getRegion("time").replace(":%S",""))
    return (local_date, local_time)
    
def normalize_string(text):
    text = text.replace(":", "")
    text = text.replace("/", "-")
    text = text.replace("\\", "-")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("*", "")
    text = text.replace("?", "")
    text = text.replace('|', "")
    text = text.replace('(', "")
    text = text.replace(')', "")
    text = text.replace("\"","")
    text = text.strip()
    text = text.rstrip('.')
    text = unicodedata.normalize('NFKD', try_decode(text))
    return text
    
def get_compare_string(text):
    '''strip special chars in a string for better comparing of searchresults'''
    if not isinstance(text, unicode):
        text.decode("utf-8")
    text = text.lower()
    text = ''.join(e for e in text if e.isalnum())
    return text
    
def strip_newlines(text):
    '''strip any newlines from a string'''
    return text.replace('\n', ' ').replace('\r', '').rstrip()

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
