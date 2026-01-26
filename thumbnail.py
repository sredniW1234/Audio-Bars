import yt_dlp, urllib.request as urllib


def fetch_thumbnail(title, player: str) -> str:
    """Fetches the thumbnail URL from YouTube based on the title and player name."""

    # Check if the player is a browser
    browser_players = ["chrome", "firefox", "edge", "opera", "brave"]
    if not any(browser in player.lower() for browser in browser_players):
        return None

    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{title}", download=False)
        return info["entries"][0]["thumbnail"]


def save_thumbnail(thumbnail_url, filename: str):
    """Saves the thumbnail image to a file."""
    print(thumbnail_url)
    if thumbnail_url is None:
        return
    request = urllib.Request(thumbnail_url)
    pic = urllib.urlopen(request)
    print("downloading: " + thumbnail_url)
    print(filename)
    # urllib.urlretrieve(self.url, filePath)
    with open(filename, "wb") as localFile:
        localFile.write(pic.read())
