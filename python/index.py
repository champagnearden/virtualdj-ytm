import os, urllib.parse
import requests as rq

SEPARATOR = '\u2022'
FORMAT = "m4a"
VIDEO_URL = "https://music.youtube.com/watch?v="
OUTPUT_PATH = os.path.expanduser("~")+"/.virtualdj-ytm/Downloads"
TITLE = "title"
VIDEO_ID = "video_id"
ARTIST = "artist"
ALBUM = "album"
DURATION = "duration"
THUMBNAILS_URL = "thumbnails"

def download_song(song: dict):
    video_id = song[VIDEO_ID]
    filename = f"{song[TITLE]} - {song[ARTIST]}.{FORMAT}"

    if os.path.isfile(os.path.join(OUTPUT_PATH, filename)):
        print(f"{filename} already downloaded !")
        return
    
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    command = "yt-dlp -f bestaudio[ext={}] --extract-audio --audio-format {} -o \"{}/{}\" \"{}\"".format(FORMAT, FORMAT, OUTPUT_PATH, filename, VIDEO_URL + video_id)
    print(command)
    result = os.system(command)
    if result == 0:
        print("Download successfull")
    else:
        print(f"Error downloading {filename}")
    
def get_artist(path, i=0) -> str:
    ret=""
    while i < len(path):
        current = path[i]["text"]
        if current.find(SEPARATOR):
            break
        ret += current
        i+=1
    return ret

def get_prefix_index(prefix, key):
    for i in range(len(prefix)):
        if prefix[i].get(key):
            return i
    return -1

def perform_post_request(query):
    encoded_query = urllib.parse.quote(query)
    headers = {"Content-Type": "application/json; charset=utf-8"}
    body_request = {
        "context": {
            "client": {
                "clientName": "WEB_REMIX",
                "clientVersion": "1.20240911.01.00"
            }
        },
        "query": encoded_query
    }

    try:
        response = rq.post( 
            "https://music.youtube.com/youtubei/v1/search?prettyPrint=false",
            headers=headers, 
            json=body_request
        )

        if (response.status_code == 200):
            rep = response.json()
            prefix = rep["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"] # never changes
            prefix_index = get_prefix_index(prefix, "musicCardShelfRenderer")
            infos = prefix[prefix_index]["musicCardShelfRenderer"]["subtitle"]["runs"]
            for offset in range(len(prefix)):
                if "musicShelfRenderer" in prefix[offset].keys():
                    if prefix[offset]["musicShelfRenderer"]["title"]["runs"][0]["text"] == "Songs":
                        break
            search = [dict() for _ in range(len(prefix[offset]["musicShelfRenderer"]["contents"])+1)]
            search[0][TITLE] = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["text"]
            search[0][ARTIST] = infos[prefix_index + 1]["text"]
            search[0][ALBUM] = infos[4]["text"] if "navigationEndpoint" in infos[prefix_index + 3].keys() else "undefined"
            search[0][THUMBNAILS_URL] = prefix[prefix_index]["musicCardShelfRenderer"]["thumbnail"]["musicThumbnailRenderer"]["thumbnail"]["thumbnails"]

            video_id_prefix = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]
            # wether the song is a podcast / an episode or a regular song, youtube handles it differently
            if ("browseEndpoint" in video_id_prefix.keys()):
                search[0][VIDEO_ID] = video_id_prefix["browseEndpoint"]["browseId"]
                search[0][DURATION] = "NOT AN ACTUAL SONG"
            else:
                search[0][VIDEO_ID] = video_id_prefix["watchEndpoint"]["videoId"]
                search[0][DURATION] = infos[prefix_index + 5]["text"]
            
            for i in range(len(prefix[offset]["musicShelfRenderer"]["contents"])): 
                search[i+1][TITLE] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"]
                search[i+1][ARTIST] = get_artist(prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"])
                search[i+1][ALBUM] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][2]["text"]
                search[i+1][DURATION] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][4]["text"]
                search[i+1][VIDEO_ID] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"]
                search[i+1][THUMBNAILS_URL] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["thumbnail"]["musicThumbnailRenderer"]["thumbnail"]["thumbnails"]
            
            # display the search element
            for x in range(len(search)):
                print(f"~[{x}]~")
                
                for k, v in search[x].items():
                    print(f" {k}: {v}")
                
                print('-' * 30)
            return search
        else:
            print(f"Error: {response.status_code}")
            raise rq.RequestException(response.json()["error"])
    except Exception as e:
        print("Error: unable to perform the request")
        print(e)
        return dict()
    
def main():
    print("Welcome to VirtualDj-YoutubeMusic")
    index = 0
    while(True):
        try: 
            query = input("Enter your search query: ")
            print("#" *30)
            if query == "exit": raise KeyboardInterrupt
            search = perform_post_request(query)
            if len(search) > 0:
                song_index = int(input(f"Choose index [1-{len(search)}] (0 to go back to search): "))
                if index == 0: continue
                download_song(search[song_index-1])
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()