#include <iostream>
#include <cpr/cpr.h>        // Include CPR for HTTP requests
#include <nlohmann/json.hpp> // Include nlohmann/json for JSON handling
#include <cstdlib>
#include <filesystem>
#include <curl/curl.h>
#include <signal.h>

#pragma execution_character_set("utf-8")

using namespace std;
using namespace cpr;
using json = nlohmann::json;
// Please youtube, never change the separator
const char8_t SEPARATOR[] = u8"\u2022";
const string FORMAT = "m4a";
const string VIDEO_URL = "https://music.youtube.com/watch?v=";

const string TITLE = "title";
const string VIDEO_ID = "video_id";
const string ARTIST = "artist";
const string ALBUM = "album";
const string DURATION = "duration";

#ifdef _WIN32
const char* getHomeDirectory() {
    return getenv("USERPROFILE");  // Windows: %USERPROFILE%
}
#else
const char* getHomeDirectory() {
    return getenv("HOME");  // Linux/macOS: $HOME
}
#endif
static void print(string args) {
    cout << args << endl;
}

void downloadYouTubeAsMP3(const json& song) {
    const string videoId = song[VIDEO_ID];
    const string outputPath = string(getHomeDirectory()) + "/.virtualdj-ytm/Downloads";
    const string fileName = string(song[TITLE])+"-"+string(song[ARTIST])+"."+FORMAT;

    // if outputPath/videoId.FORMAT is not found then download it
    if (filesystem::is_regular_file(outputPath+"/"+fileName)) {
        print("file aleready downloaded !");
        return;
    }
    filesystem::create_directories(outputPath);
    // Construct the yt-dlp command
    string command = format("yt-dlp -f bestaudio[ext={}] --extract-audio --audio-format {} -o \"{}/{}\" \"{}\"", FORMAT, FORMAT, outputPath, fileName, VIDEO_URL + videoId);
    print(command);
    // Call system() to execute the command
    int result = std::system(command.c_str());

    if (result == 0) {
        print("Download and conversion to m4a succeeded!");
    }
    else {
        print("Error: Download and conversion failed.");
    }
}

string getArtist(const json& path, int i=0) {
    
    string ret = "";
    while (i < path.size()) {
        string current = path[i]["text"];
        if (current.find(reinterpret_cast<const char*>(SEPARATOR)) != string::npos) {
            break;
        }
        ret += current;
        i++;
    }
    return ret;
}

vector<map <string, string>> performPostRequest(const string& query) {
    // Create the JSON body dynamically
    CURL* curl = curl_easy_init();
    if (curl) {
        char* encodedQuery = curl_easy_escape(curl, query.c_str(), 0);
        json bodyRequest = {
            {"context", {
                {"client", {
                    {"clientName", "WEB_REMIX"},
                    {"clientVersion", "1.20240911.01.00"}
                }}
            }},
            {"query", encodedQuery}
        };
        // Convert the JSON object to a string
        string requestBody = bodyRequest.dump();

        // Perform the POST request using CPR
        Response response = Post(
            Url{ "https://music.youtube.com/youtubei/v1/search?prettyPrint=false" },
            Header{ {"Content-Type", "application/json"} },
            Body{ requestBody }
        );
        // Check if the request was successful
        if (response.status_code == 200) {
            //print(format("Response: {}", response.text));
            json rep = json::parse(response.text);
            try {
                json prefix = rep["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]; // never changes
                const int prefix_index = prefix[1].contains("itemSectionRenderer") ? 2 : 1; // take the results even if yt thinks that there is a spelling check
                json infos = prefix[prefix_index]["musicCardShelfRenderer"]["subtitle"]["runs"];
                vector<map <string, string>>search(4);

                search[0][TITLE] = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["text"];
                search[0][ARTIST] = infos[prefix_index + 1]["text"];
                search[0][ALBUM] = infos[prefix_index + 3].contains("navigationEndpoint") ? infos[4]["text"] : "undefined";
                json videoIdPrefix = prefix[prefix_index]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"];
                //wether the song is a podcast / an episode or a regular song, youtube handles it differently
                if (videoIdPrefix.contains("browseEndpoint")) {
                    search[0][VIDEO_ID] = videoIdPrefix["browseEndpoint"]["browseId"];
                    search[0][DURATION] = "NOT AN ACTUAL SONG";
                }
                else {
                    search[0][VIDEO_ID] = videoIdPrefix["watchEndpoint"]["videoId"];
                    search[0][DURATION] = infos[prefix_index + 5]["text"];
                }
                int offset = 0;
                while (offset < prefix.size() && prefix[offset]["musicShelfRenderer"]["title"]["runs"][0]["text"] != "Songs") {
                    offset++;
                }
                for (int i = 0; i < prefix[offset]["musicShelfRenderer"]["contents"].size(); i++) {
                    search[i+1][TITLE] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"];
                    search[i+1][ARTIST] = getArtist(prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"]);
                    search[i+1][ALBUM] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][2]["text"];
                    search[i+1][DURATION] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][4]["text"];
                    search[i+1][VIDEO_ID] = prefix[offset]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"];
                }

                // display the search element
                for (int x = 0; x < search.size(); x++) {
                    print(format("~[{}]~", x));
                    map<string, string>::iterator i = search[x].begin();
                    while (i != search[x].end()) {
                        string k = (*i).first;
                
                        print(format(" {}: {}", k, search[x][k]));
                        i++;
                    }
                    print(string(30,'-'));
                }
                return search;
            }
            catch (exception e) {
                cout << "Error accessing JSON field: " << e.what() << endl;
            }
        }
        else {
            print(format("POST request failed with status code: {}", response.status_code));
        }
        curl_free(encodedQuery);  // Free the encoded query string
        curl_easy_cleanup(curl);
    }
    else {
        print("unable to initialize curl");
    }
    vector<map <string, string>> mt(0);
    return mt;
}

void signal_callback_handler(int signum) {
    print("Exiting program");
    exit(0);
}

int main() {
    SetConsoleOutputCP(65001);
    print("Welcome to VirtualDj-YoutubeMusic");
    string query="";  // The dynamic query parameter
    short index=0;
    signal(SIGINT, signal_callback_handler);
    while (true) {
        cout << "Search query: ";
        getline(cin, query);
        print(string(30, '#'));
        vector<map <string, string>> search = performPostRequest(query); // Perform the POST request
        print(format("Choisir index [1-{}] (0 to go back to search): ",search.size()));
        cin >> index;
        cin.ignore();
        if (index == 0) {
            continue;
        }
        downloadYouTubeAsMP3(search[index]);
    }
    return EXIT_SUCCESS;
}
