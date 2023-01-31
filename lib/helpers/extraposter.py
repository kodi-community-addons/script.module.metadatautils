#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    extraposter.py
    Get extraposter location for kodi media
"""

import os, sys
import xbmcvfs


def get_extraposter(file_path):
    """get extraposter path on disk based on media path"""
    result = {}
    efap_path = ""
    if "plugin.video.emby" in file_path:
        # workaround for emby addon
        efap_path = "plugin://plugin.video.emby/extraposter?path=" + file_path
    elif "plugin://" in file_path:
        efap_path = ""
    elif "videodb://" in file_path:
        efap_path = ""
    else:
        count = 0
        while not count == 3:
            # lookup extraposter folder by navigating up the tree
            file_path = os.path.dirname(file_path)
            try_path = file_path + "/extraposter/"
            if xbmcvfs.exists(try_path):
                efap_path = try_path
                break
            count += 1

    if efap_path:
        result["art"] = {"extraposter": efap_path}
        for count, file in enumerate(xbmcvfs.listdir(efap_path)[1]):
            if file.lower().endswith(".jpg"):
                result["art"]["ExtraPoster.%s" % count] = efap_path + file
    return result
