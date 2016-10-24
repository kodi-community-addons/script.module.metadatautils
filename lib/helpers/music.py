#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import log_msg
from simplecache import SimpleCache

class MusicArt(object):
    '''get images from google images'''
    
    def __init__(self, *args):
        self.cache = SimpleCache()
    