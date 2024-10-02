#include <iostream>
#include <cpr/cpr.h>        // Include CPR for HTTP requests
#include <nlohmann/json.hpp> // Include nlohmann/json for JSON handling
#include <cstdlib>
#include <filesystem>

using namespace std;
using namespace cpr;
using json = nlohmann::json;
// Please youtube, never change the separator
const char8_t SEPARATOR[] = u8"\u2022";
const string FORMAT = "m4a";
const string VIDEO_URL = "https://music.youtube.com/watch?v=";
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

void downloadYouTubeAsMP3(const string& videoId) {
    const string videoUrl = VIDEO_URL + videoId;
    const string outputPath = string(getHomeDirectory()) + "/.virtualdj-ytm/Downloads";

    // if outputPath/videoId.FORMAT is not found then download it
    if (filesystem::is_regular_file(format("{}/{}.{}",outputPath, videoId, FORMAT))) {
        print("file aleready downloaded !");
        return;
    }
    filesystem::create_directories(outputPath);
    // Construct the yt-dlp command
    string command = format("yt-dlp -f bestaudio[ext={}] --extract-audio --audio-format {} -o {}/{}.{} \"{}\"", FORMAT, FORMAT, outputPath, videoId, FORMAT, videoUrl);
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

json performPostRequest(const string& query) {
    // Create the JSON body dynamically
    json bodyRequest = {
        {"context", {
            {"client", {
                {"clientName", "WEB_REMIX"},
                {"clientVersion", "1.20240911.01.00"}
            }}
        }},
        {"query", query}
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
            json prefix = rep["contents"]["tabbedSearchResultsRenderer"]["tabs"][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"];
            json infos = prefix[1]["musicCardShelfRenderer"]["subtitle"]["runs"];
            const int length = prefix[2]["musicShelfRenderer"]["contents"].size();
            vector<map <string, string>>search(length+1);

            search[0]["title"] = prefix[1]["musicCardShelfRenderer"]["title"]["runs"][0]["text"];
            search[0]["video_id"] = prefix[1]["musicCardShelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"];
            search[0]["artist"] = infos[2]["text"];
            search[0]["album"] = infos[4].contains("navigationEndpoint") ? infos[4]["text"]: "undefined";
            search[0]["duration"] = infos[6]["text"];

            for (int i = 0; i < length; i++) {
                search[i+1]["title"] = prefix[2]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["text"];
                search[i+1]["artist"] = getArtist(prefix[2]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"]);
                search[i+1]["album"] = prefix[2]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][2]["text"];
                search[i+1]["duration"] = prefix[2]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][1]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][4]["text"];
                search[i+1]["video_id"] = prefix[2]["musicShelfRenderer"]["contents"][i]["musicResponsiveListItemRenderer"]["flexColumns"][0]["musicResponsiveListItemFlexColumnRenderer"]["text"]["runs"][0]["navigationEndpoint"]["watchEndpoint"]["videoId"];
            }

            // display the search element
            for (int x = 0; x < search.size(); x++) {

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
        catch (json::exception e) {
            cout << "Error accessing JSON field: " << e.what() << endl;
        }
    }
    else {
        print(format("POST request failed with status code: {}", response.status_code));
    }
}

int main() {
    string query;  // The dynamic query parameter
    cout << "Search query: ";
    cin >> query;
    print(string(30, '#'));
    vector<map <string, string>> search = performPostRequest(query); // Perform the POST request
    short index;
    print(format("Choisir index [O-{}]: ",search.size()-1));
    cin >> index;
    downloadYouTubeAsMP3(search[index]["video_id"]);
    return 0;
}
