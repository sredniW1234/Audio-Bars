import yt_dlp, urllib.request as urllib
import threading


class Thumbnail:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

    def _fetch_thumbnail(self, title: str, player: str) -> str:
        """Fetches the thumbnail URL from YouTube based on the title and player name."""

        # Check if the player is a browser
        browser_players = ["chrome", "firefox", "edge", "opera", "brave"]
        if not any(browser in player.lower() for browser in browser_players):
            return ""

        ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{title}", download=False)
                return info["entries"][0]["thumbnail"]
        except Exception as e:
            print("Error fetching thumbnail:", str(e))
            return ""

    def _save_thumbnail(self, thumbnail_url: str, filename: str):
        """Saves the thumbnail image to a file."""
        if thumbnail_url == "":
            return
        request = urllib.Request(thumbnail_url)
        pic = urllib.urlopen(request)
        # urllib.urlretrieve(self.url, filePath)
        with open(filename, "wb") as localFile:
            localFile.write(pic.read())

    def get_thumbnail(self, title: str, player: str) -> None:
        def _get(title: str, player: str, event: threading.Event):
            url = self._fetch_thumbnail(title, player)
            if event.is_set():
                return
            self._save_thumbnail(url, "thumbnail.png")

        self._stop_event.set()
        self._stop_event = threading.Event()
        event = self._stop_event
        self.thread = threading.Thread(
            target=_get, args=[title, player, event], daemon=True
        )
        self.thread.start()
