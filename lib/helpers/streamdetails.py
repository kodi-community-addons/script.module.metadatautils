#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    script.module.metadatautils
    streamdetails.py
    Get all streamdetails for a kodi media item in database
"""

import os, sys

def get_streamdetails(kodidb, db_id, media_type):
    """helper to get all streamdetails from a video item in kodi db"""
    streamdetails = {}
    # get data from json
    if "movie" in media_type and "movieset" not in media_type:
        json_result = kodidb.movie(db_id)
    elif "episode" in media_type:
        json_result = kodidb.episode(db_id)
    elif "musicvideo" in media_type:
        json_result = kodidb.musicvideo(db_id)
    else:
        json_result = {}

    if json_result and json_result["streamdetails"]:
        audio = json_result["streamdetails"]['audio']
        subtitles = json_result["streamdetails"]['subtitle']
        video = json_result["streamdetails"]['video']
        all_audio_str = []
        all_subs = []
        all_lang = []
        for count, item in enumerate(audio):
            # audio codec
            codec = item['codec']
            if "ac3" in codec:
                codec = "Dolby D"
            elif "dca" in codec:
                codec = "DTS"
            elif "dts-hd" in codec or "dtshd" in codec:
                codec = "DTS HD"
            # audio channels
            channels = item['channels']
            if channels == 1:
                channels = u"1.0"
            elif channels == 2:
                channels = "2.0"
            elif channels == 3:
                channels = "2.1"
            elif channels == 4:
                channels = "4.0"
            elif channels == 5:
                channels = "5.0"
            elif channels == 6:
                channels = "5.1"
            elif channels == 7:
                channels = "6.1"
            elif channels == 8:
                channels = "7.1"
            elif channels == 9:
                channels = "8.1"
            elif channels == 10:
                channels = "9.1"
            else:
                channels = str(channels)
            # audio language
            language = item.get('language', '')
            if language and language not in all_lang:
                all_lang.append(language)
            if language:
                streamdetails['AudioStreams.%d.Language' % count] = item['language']
            if item['codec']:
                streamdetails['AudioStreams.%d.AudioCodec' % count] = item['codec']
            if item['channels']:
                streamdetails['AudioStreams.%d.AudioChannels' % count] = str(item['channels'])
            joinchar = " • "
            audio_str = joinchar.join([language, codec, channels])
            if audio_str:
                streamdetails['AudioStreams.%d' % count] = audio_str
                all_audio_str.append(audio_str)
        subs_count = 0
        subs_count_unique = 0
        for item in subtitles:
            subs_count += 1
            if item['language'] not in all_subs:
                all_subs.append(item['language'])
                streamdetails['Subtitles.%d' % subs_count_unique] = item['language']
                subs_count_unique += 1
        streamdetails['subtitles'] = all_subs
        streamdetails['subtitles.count'] = str(subs_count)
        streamdetails['allaudiostreams'] = all_audio_str
        streamdetails['audioStreams.count'] = str(len(all_audio_str))
        streamdetails['languages'] = all_lang
        streamdetails['languages.count'] = len(all_lang)
        if len(video) > 0:
            stream = video[0]
            streamdetails['videoheight'] = stream.get("height", 0)
            streamdetails['videowidth'] = stream.get("width", 0)
    if json_result.get("tag"):
        streamdetails["tags"] = json_result["tag"]
    return streamdetails
