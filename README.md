# yt-dlp info reader agent.

A Plex YouTube agent that works closely with yt-dlp info files require no internet connection. 

## What is the required directory structure?

The required structure for the agent to work is the following

```
- Channel/Playlist name [`id`]
- Channel/Playlist name [`id`].jpg
- Channel/Playlist name [`id`].info.json
-- Season XXXX
--- YYYYMMDD title [id].mp4
--- YYYYMMDD title [id].jpg
--- YYYYMMDD title [id].info.json
```

The `id` can be in the following format `[youtube-(id)]` or `[(id)]`. This agent does not support multiple playlists in single parent directory.
While the `id` is *REQUIRED* on the main channel/playlist directory, you can omit them for the video files themselves, however we suggest to keep them.


This agent requires the `jp_scanner.py` for scanning media.


## How to download channel / play list `info.json`?

```bash
$ yt-dlp -I0 --write-info-json --write-thumbnail --convert-thumbnails jpg -o "%(title)s [%(id)s]/%(title).180B [%(id)s].%(ext)s" --paths /media/youtube https://www.youtube.com/channel/UCRF6lN9YOQrtDQCi-rOlP7g
```
Change `/media/youtube` to root of your YouTube library. And `https://www.youtube.com/channel/UCRF6lN9YOQrtDQCi-rOlP7g` to the channel/playlist URL.
You only need to do this once, However to get updated metadata/photo from the channel you need to run the command again. to replace the old data. and refresh metadata from plex.

## What does this agent do differently compared to the other YouTube agents?
This local only agent, and as such it does not suffer from missing metadata if the video files are deleted from YouTube. I Also mainly developed this plugin to be in use with my other project `arabcoders/watchstate`. which is used to sync play state between media servers. And i have similar agent for both jellyfin and emby.

## Video files naming?
The video files should be in the following naming format `YYYYMMDD title [id]` with both `info.json` and `.jpg` file. which is somewhat is required for `jp_scanner.py` to work. You can use the following command which i personally use

```bash
$ yt-dlp -I0 --write-info-json --write-thumbnail --convert-thumbnails jpg -o "%(title)s [%(id)s]/Season %(release_date>%Y,upload_date>%Y|Unknown)s/%(release_date>%Y%m%d,upload_date>%Y%m%d)s - %(title).180B [%(extractor)s-%(id)s].%(ext)s" --paths /media/youtube https://www.youtube.com/watch?v=d_pVmR_0p0E
```

# Is other photo extensions supported?
Yes, the following format are supported. `".jpg", ".jpeg", ".webp", ".png", ".tiff", ".gif", ".jp2"`.

## Installation
In order to use this Agent you need to use the [jp_scanner.py](https://gist.github.com/arabcoders/ecb2755aa1d76dc89301ec44b8d367d5), and
save it into `[...]/Plex Media Server/Scanners/Series/jp_scanner.py` if you don't know there are more detailed guide at this link [How to install a Scanner](https://github.com/ZeroQI/Absolute-Series-Scanner#install--update).

1. Go to the release page and download latest version.
2. Unzip the file and rename the main directory to be `ytinforeader.bundle` Make sure the `Contents` directory is directly underneath `ytinforeader.bundle`. 
3. Move the folder into the "Plug-ins" folder in your Plex Media Server installation ([Wait where?](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/))
4. Create a new (or update an existing) library and select "TV Show"
5. Click on the "Advanced" tab and select
    1. Scanner: jp_scanner
    2. Agent: yt-dlp info reader agent.

Now you are done. At first Plex will scan for all the files, when this is done the agent will attempt to find the metadata associated with the videos.