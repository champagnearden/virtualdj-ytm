from typing import List
class Song:
    def __init__(self, title:str, artist:str, album:str, duration:str, thumbnail_url:List[str], video_id:str):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration
        self.thumbnail_url = thumbnail_url
        self.video_id = video_id

    def __str__(self):
        return f"Title: {self.title}\nArtist: {self.artist}\nAlbum: {self.album}\nDuration: {self.duration}\nThumbnail URL: {self.thumbnail_url}\nVideo ID: {self.video_id}"
