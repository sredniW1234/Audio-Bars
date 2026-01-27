import syncedlyrics as sl
import threading


class Lyrics:
    def __init__(self, title: str, artist: str) -> None:
        self.title = title
        self.artist = artist
        self.timed_lyrics = {}
        self.lock = threading.Lock()
        self.clean_title()

    def clean_title(self) -> str:
        title = self.title
        terms = [
            "official lyrics video",
            "official cover video",
            "official lyric video",
            "official music video",
            "official video",
            "official audio",
            "official amv",
            "lyrics video",
            "lyric video",
            "visualizer",
            "remastered",
            "remaster",
            "lyrics",
            "lyric",
            "cover",
            "cc",
        ]
        surrounding = ["[]", "()", "{}"]
        for outer in surrounding:
            for term in terms:
                title = title.lower().replace(outer[0] + term + outer[1], "").strip()
        self.title = title
        return self.title

    def search(self) -> str:
        lyrics = sl.search(
            search_term=f"{self.title} {self.artist}",
            synced_only=True,
            providers=["Lrclib", "Musixmatch", "AZLyrics"],
        )
        return lyrics or ""

    def _lrc_time_to_seconds(self, lrc_time: str) -> int:
        lrc_times = lrc_time.split(":")

        HOUR_MILLISECONDS = 3.6e6
        MINUTE_MILLISECONDS = 60000
        SECOND_MILLESECONDS = 1000
        time = 0
        if len(lrc_times) == 3:
            # hours
            time += int(lrc_times[0]) * HOUR_MILLISECONDS
            lrc_times.pop(0)
        time += int(lrc_times[0]) * MINUTE_MILLISECONDS
        time += int(lrc_times[1].split(".")[0]) * SECOND_MILLESECONDS
        time += int(lrc_times[1].split(".")[1])

        return int(time / 1000)  # Converting back to seconds

    def parse(self, lyrics: str) -> dict:
        timed_lyrics = {}
        if lyrics == "":
            return {-1: "No Lyrics Available."}
        for line in lyrics.splitlines():
            time = line[:11].strip()
            if len(line) < 2 or not line[1].isnumeric():
                continue
            if time[-1] != "]":
                # Hours
                time = line[:14].strip()
                if time[-1] != "]":
                    # Just return bc who has a video thats more than xx hours long?
                    return {}
                time = time[1:12].strip()
            else:
                time = time[1:9].strip()
            timed_lyrics[self._lrc_time_to_seconds(time)] = line[11:]

        return timed_lyrics

    def retrieve(self):
        def get():
            lyrics = self.parse(self.search())
            with self.lock:
                self.timed_lyrics = lyrics
            print("\033c", end="")  # In case of error, clear console

        self.thread = threading.Thread(target=get)
        self.thread.start()

    def get_lyric(self, time: int):
        if self.timed_lyrics.get(-1):
            return self.timed_lyrics.get(-1)
        return self.timed_lyrics.get(time, "")
