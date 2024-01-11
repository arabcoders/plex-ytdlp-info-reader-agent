#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import re
import json
from io import open
import traceback
import urllib


RX_CHANNEL_ID = re.compile(
    r'(?<=\[)(?:youtube-)?(?P<id>(UC|HC)[a-zA-Z0-9\-_]{22})(?=\])', re.IGNORECASE)

RX_PLAYLIST_ID = re.compile(
    r'\[(?:youtube\-)?(?P<id>PL[^\[\]]{32}|PL[^\[\]]{16}|(UU|FL|LP|RD)[^\[\]]{22})\]', re.IGNORECASE)

RX_VIDEO_ID = re.compile(
    r'(?<=\[)(?:youtube-)?(?P<id>[a-zA-Z0-9\-_]{11})(?=\])', re.IGNORECASE)


def Start():
    Log("Starting up ...")


class YTDLPInfoReaderAgent(Agent.TV_Shows):
    img_exts = [".jpg", ".jpeg", ".webp", ".png", ".tiff", ".gif", ".jp2"]

    name = 'yt-dlp info reader agent'
    primary_provider = True
    fallback_agent = None
    contributes_to = None
    accepts_from = ['com.plexapp.agents.xbmcnfotv',
                    'com.plexapp.agents.localmedia']
    languages = [Locale.Language.NoLanguage]

    def dump(self, obj):
        data = []
        for attr in dir(obj):
            data.append("%s = %s" % (attr, getattr(obj, attr)))
        return data

    def getShowInfo(self, filename):
        info = {}
        filename = urllib.unquote(filename).decode('utf8')
        dirName = os.path.dirname(os.path.dirname(filename))
        parentDirName = os.path.basename(dirName)
        Log(u"getShowInfo() - filename: {} dirName: {} parentDirName: {}".format(
            filename,
            dirName,
            parentDirName
        ))

        try:
            channelId = None

            channel = RX_CHANNEL_ID.search(parentDirName)
            if channel:
                channelId = channel.group('id')
            else:
                playlist = RX_PLAYLIST_ID.search(parentDirName)
                if playlist:
                    channelId = playlist.group('id')

            if not channelId:
                Log(u"getShowInfo() - No channel or playlist ID in parent directory name: {}.".format(parentDirName))
                return None

            Log(u"getShowInfo() - Found ID: {}".format(channelId))

            jsonFile = None
            files = os.listdir(dirName)
            for file in files:
                baseFile = os.path.basename(file)
                if channelId in baseFile and file.endswith(".info.json"):
                    jsonFile = os.path.join(dirName, file)
                    break

            if not jsonFile:
                Log(u"getShowInfo() - No yt-dlp .info.json file was found in: {}.".format(dirName))
                return None

            imgFile = None
            for file in files:
                baseFile = os.path.basename(file)
                if channelId in baseFile and file.endswith(tuple(self.img_exts)):
                    imgFile = os.path.join(dirName, file)
                    break

            Log(u"getShowInfo() - Found yt-dlp json file: {}".format(jsonFile))
            with open(jsonFile, encoding="utf-8") as json_data:
                data = json.load(json_data)

            info['id'] = channelId

            if imgFile:
                info['poster'] = imgFile

            if 'title' in data:
                info['title'] = data['title'].strip()
            elif 'channel' in data:
                info['title'] = data['channel'].strip()
            else:
                info['title'] = data['uploader'].strip()

            info['summary'] = data['description'].strip(
            ) if data['description'] else ''
            info['tags'] = data['tags'] if 'tags' in data else []
            info['studio'] = data['uploader'].strip()

            Log(u"getShowInfo() - info: {}".format(info))

            return info
        except Exception as e:
            Log(u'getShowInfo() Exception: {}'.format(e))
            Log(u'getShowInfo() Traceback: {}'.format(traceback.format_exc()))
            pass

        return None

    def getFile(self, media):
        if not media or not media.seasons:
            return None

        for s in media.seasons:
            for e in media.seasons[s].episodes:
                file = media.seasons[s].episodes[e].items[0].parts[0].file
                if not file:
                    continue
                return file

        return None

    def search(self, results, media, lang, manual=False):
        Log("".ljust(60, '='))
        Log(u"Search() - Looking for: {}".format(media.show))
        Log("".ljust(60, '='))
        json = self.getShowInfo(media.filename)
        if not json:
            Log(u"Search() - No results found for: [{}]".format(media.show))
            return

        results.Append(
            MetadataSearchResult(
                id=json.get('id'),
                name=json.get('title'),
                year=None,
                lang=lang,
                score=100
            ))

        results.Sort('score', descending=True)

    def update(self, metadata, media, lang):
        Log("".ljust(60, '='))
        Log("Entering update function")
        Log("".ljust(60, '='))

        # Get the path to an media file to process channel data.
        filename = self.getFile(media)
        if not filename:
            Log("Update(): Couldnt find media file to treverse the directory tree.")
            return

        channelData = self.getShowInfo(filename)
        if not channelData:
            Log("Update(): Couldnt find channel data.")
            return

        metadata.title = channelData['title'].strip()
        metadata.studio = channelData['studio'].strip()
        metadata.summary = channelData['summary'].strip()

        if 'poster' in channelData:
            picture = Core.storage.load(channelData['poster'])
            picture_hash = hashlib.md5(picture).hexdigest()
            metadata.posters[picture_hash] = Proxy.Media(picture, sort_order=1)

        if 'tags' in channelData:
            for tag in channelData['tags']:
                metadata.collections.add(tag.strip())

        @parallelize
        def UpdateEpisodes():
            for s in media.seasons:
                for e in media.seasons[s].episodes:
                    episode = metadata.seasons[s].episodes[e]
                    episode_file = media.seasons[s].episodes[e].items[0].parts[0].file

                    @task
                    def updateEpisode(episode=episode, episode_file=episode_file, metadata=metadata):
                        filepath, _ = os.path.splitext(episode_file)
                        filepath = filepath.strip()

                        Log("updateEpisode() Processing: [{}] in [{}]".format(
                            episode_file, metadata.title))

                        # Check if there is a thumbnail for this episode
                        for extension in self.img_exts:
                            maybeFile = filepath + extension
                            if os.path.isfile(maybeFile):
                                Log("updateEpisode() Found thumbnail {}".format(
                                    maybeFile))
                                # we found an image, attempt to create an Proxy Media object to store it
                                try:
                                    picture = Core.storage.load(maybeFile)
                                    picture_hash = hashlib.md5(
                                        picture).hexdigest()
                                    episode.thumbs[picture_hash] = Proxy.Media(
                                        picture, sort_order=1)
                                    break
                                except Exception as e:
                                    Log("updateEpisode() Could not access file [{}]. {}".format(
                                        maybeFile, str(e)))

                        # Attempt to open the .info.json file Youtube-DL stores.
                        try:
                            with open(filepath + ".info.json", encoding="utf-8") as json_file:
                                data = json.load(json_file)

                            if 'fulltitle' in data:
                                episode.title = data['fulltitle'].strip()

                            if 'description' in data:
                                episode.summary = data["description"].strip()

                            if 'upload_date' in data:
                                episode.originally_available_at = Datetime.ParseDate(
                                    data['upload_date']).date()
                                if metadata.originally_available_at is None:
                                    metadata.originally_available_at = episode.originally_available_at

                            if 'average_rating' in data and data['average_rating'] is not None:
                                episode.rating = (data['average_rating'] * 2)

                            Log("updateEpisode() Processed successfully! This episode was named [{}].".format(
                                data['fulltitle']))
                        except IOError as e:
                            # Attempt to make a title out of the filename
                            episode.title = re.sub(
                                '\[.{11}\]', '', os.path.basename(filepath)).strip()
                            Log("updateEpisode() Could not access file [{}], named the episode [{}]. Error [{}]".format(
                                filepath + ".info.json", episode.title, str(e)))
