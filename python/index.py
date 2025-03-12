from os import path, makedirs, system
from typing import List, Tuple
from requests import post, RequestException
from song import Song
from logger import Logger

SEPARATORS = [' & ', ', ']
FORMAT = "m4a"
VIDEO_URL = "https://music.youtube.com/watch?v="
OUTPUT_PATH = path.expanduser("~").replace("\\", "/")+"/.virtualdj-ytm/Downloads"

def download_song(song: Song, path_folder=OUTPUT_PATH):
    video_id = song.video_id
    filename = f"{song.title} - {song.artist}.{FORMAT}"

    if path.isfile(path.join(path_folder, filename)):
        print(f"{filename} already downloaded !")
        return
    
    if not path.exists(path_folder):
        makedirs(path_folder)
    
    print(path_folder)
    command = "yt-dlp -f bestaudio[ext={}] --extract-audio --audio-format {} -o \"{}/{}\" \"{}\"".format(FORMAT, FORMAT, path_folder, filename, VIDEO_URL + video_id)
    result = system(command)
    if result == 0:
        print("Download successfull")
    else:
        print(f"Error downloading {filename}")
    
def get_artist(p) -> Tuple[str, int]:
    ret=p[0]["text"]
    # get the indexes of separators
    indexes = [i for i in range(len(p)) if p[i]["text"] in SEPARATORS]
    for i, esp in enumerate(indexes):
        ret+=SEPARATORS[0] if i==len(indexes)-1 else SEPARATORS[1]
        ret+=p[2*(i+1)]["text"]
    return (ret, len(indexes)*2)

def get_prefix_index(prefix, key) -> int:
    for i in range(len(prefix)):
        if prefix[i].get(key):
            return i
    return 1 # If recognized by youtube then it's in index 1

def get_top_result(prefix):
    logger = Logger(Logger.DEBUG)
    prefix_index = get_prefix_index(prefix, "musicCardShelfRenderer")
    sub_prefix = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]
    keys = sub_prefix.keys()
    top_result_type = ""
    if ("browseEndpoint" in keys):
        # ARTIST or PODCAST or PLAYLIST or ALBUM
        top_result_type = sub_prefix["browseEndpoint"]["browseEndpointContextSupportedConfigs"]["browseEndpointContextMusicConfig"]["pageType"]
    elif ("watchEndpoint" in keys):
        # SONG or VIDEO
        top_result_type = sub_prefix["watchEndpoint"]["watchEndpointMusicSupportedConfigs"]["watchEndpointMusicConfig"]["musicVideoType"]
    logger.log(f"Top result type: {top_result_type}", Logger.DEBUG)
    
    # Case if the top result is podcast
    if (top_result_type == "MUSIC_PAGE_TYPE_NON_MUSIC_AUDIO_TRACK_PAGE"):
        return []
    # Case if the top result is a playlist or an album
    elif (top_result_type in ["MUSIC_PAGE_TYPE_PLAYLIST", "MUSIC_PAGE_TYPE_ALBUM"]):
        return []
    # Case if the top result is an artist
    elif (top_result_type == "MUSIC_PAGE_TYPE_ARTIST"):
        # prefix[1].musicCardShelfRenderer.contents[i].musicResponsiveListItemRenderer.flexColumns[0].musicResponsiveListItemFlexColumnRenderer.text.runs[0].text
        return [
            Song(
                title = song["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"],
                artist = song["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][2]["text"],
                album = "undefined",
                thumbnail_url = song["musicResponsiveListItemRenderer"]["thumbnail"]["musicThumbnailRenderer"]["thumbnail"]["thumbnails"],
                duration = song["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"] if len(song["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"].split(":")) == 2 else "undefined",
                video_id = song["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
            ) for song in prefix[prefix_index]["musicCardShelfRenderer"]["contents"] if song["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"] == "Song"
        ]
    # Case if the top result is a song or a video
    elif (top_result_type.startswith("MUSIC_VIDEO_TYPE")):
        infos = prefix[prefix_index]["musicCardShelfRenderer"]["subtitle"]["runs"]
        return [Song(
            title = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["text"], # TITLE
            artist = infos[2]["text"], # ARTIST
            album = infos[4]["text"] if top_result_type == "MUSIC_VIDEO_TYPE_ATV" and len(infos)>5 else "undefined", # ALBUM
            thumbnail_url = prefix[prefix_index]["musicCardShelfRenderer"]["thumbnail"]["musicThumbnailRenderer"]["thumbnail"]["thumbnails"], #THUMBNAILS
            duration = infos[-1]["text"], # DURATION
            video_id = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"] # VIDEO_ID
        )]
    else:
        logger.log("Error: Top result is not a song, video, podcast, artist or playlist", Logger.ERROR)
        return []

def search_songs(query) -> List[Song]:
    logger = Logger(Logger.DEBUG)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body_request = {
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20240911.01.00"
            }
        },
        "query": query
    }

    try:
        response = post( 
            "https://music.youtube.com/youtubei/v1/search?prettyPrint=false",
            headers=headers, 
            json=body_request
        )

        if (response.status_code == 200):
            logger.log("Request successfull", Logger.DEBUG)
            rep = response.json()
            prefix = rep["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"] # never changes
            search = get_top_result(prefix)
            for offset in range(len(prefix)):
                if "musicShelfRenderer" in prefix[offset].keys():
                    if prefix[offset]["musicShelfRenderer"]["title"]["runs"][0]["text"] == "Songs":
                        break
            for i in range(len(prefix[offset]["musicShelfRenderer"]["contents"])):
                artist, offset_artist = get_artist(prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"])
                search.append(
                    Song(
                        title = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"],
                        artist = artist,
                        album = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][2+offset_artist]["text"],
                        thumbnail_url = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["thumbnail"]["musicThumbnailRenderer"]["thumbnail"]["thumbnails"],
                        duration = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][-1]["text"],
                        video_id = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
                    )
                )
            return search
        else:
            logger.log(f"Error: {response.status_code}", Logger.ERROR)
            raise RequestException(response.json()["error"])
    except Exception as e:
        logger.log("Error: unable to perform the request", Logger.ERROR)
        logger.log(e, Logger.ERROR)
        return []

def display_console(search):
    # display the search element
    for i,song in enumerate(search):
        print("~[{}]~\n{}\n{}".format(i+1,song,'-'*30))

def main():
    print("Welcome to VirtualDj-YoutubeMusic")
    index = 0
    while(True):
        try: 
            query = input("Enter your search query: ")
            print("#" *30)
            if query == "exit": raise KeyboardInterrupt
            search = search_songs(query)
            display_console(search)
            if len(search) > 0:
                index = int(input(f"Choose index [1-{len(search)}] (0 to go back to search): "))
                if index == 0: continue
                download_song(search[index-1])
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()