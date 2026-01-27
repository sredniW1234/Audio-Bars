from thumbnail import fetch_thumbnail, save_thumbnail
from audio import Stream, get_spectrum
from py_now_playing import NowPlaying
from transcriber import Lyrics
from bar import Bar, MultiBar
from ascii import AsciiImage
from asyncio import run
from time import time
import numpy as np
import os

"""
Main application to display now playing info with audio bars and ASCII art thumbnail.
Note: Requires Windows OS.
Note: Some code was generated with the help of ChatGPT. Though I have modified it, I acknowledge its assistance.
"""

# TODO: Improve ASCII art aspect ratio handling
# TODO: Don't download thumbnail and only get the PIL image in memory
# TODO: Add volume bar
# TODO: Fine tune db_range settings  --Partially done. Needs more though.
# TODO: Add command line arguments for settings
# TODO: Make bars more visually appealing
# TODO: Make Title print more pretty
# Done: Make Icon for exe
# Installer command:
# pyinstaller --onefile --console --icon=icon.ico main.py

# --- Settings ---
# Bars:
bar_total_length: int = 40  # Characters

# Spectrum:
bass_range: tuple = (20, 250)  # freq in hz
mid_range: tuple = (200, 4500)
treble_range: tuple = (4000, 20000)

bass_db_range: tuple = (-40, 40)  # minimum, maximum
mid_db_range: tuple = (-40, 20)
treble_db_range: tuple = (-50, 10)

decay: float = 0.3

# Ascii:
ascii_art = True
colored_ascii = True
ascii_size: int = 60
ascii_square: bool = False  # Doesn't look quiet correct yet, but square enough /shrug

# Lyrics:
display_lyrics = True


async def get_info(playing: NowPlaying) -> dict:
    sessions = await playing._get_sessions()
    for session in sessions:
        model_id = session.source_app_user_model_id  # type:ignore
        info = await playing.get_now_playing(model_id) or {}  # type: ignore
        info["player"] = model_id
        return info
    return {
        "title": "",
        "artist": "",
        "player": "",
    }


def update_bars(bass, mid, treble):
    bass_bar = Bar("Bass", bar_total_length, 8, True)
    mid_bar = Bar("Mid ", bar_total_length, 8, True)
    treble_bar = Bar("Treble", bar_total_length, 8, True)

    bar = MultiBar([bass_bar, mid_bar, treble_bar])
    bar.show([bass, mid, treble], get_console_width())


def compute_percent(band_magnitudes, max_val=160, use_db=False, min_db=-40, max_db=0):
    avg_mag = np.mean(band_magnitudes)
    if use_db:
        eps = 1e-10
        db = 20 * np.log10(avg_mag + eps)
        percent = (db - min_db) / (max_db - min_db)
    else:
        percent = avg_mag / max_val
    return np.clip(percent, 0, 1)


def apply_decay(prev, current, decay=0.05):
    if current >= prev:
        # rising signal: jump instantly
        return current
    else:
        # falling signal: decay gradually
        return prev * (1 - decay) + current * decay


def get_console_width():
    try:
        size = os.get_terminal_size()
        return size.columns
    except OSError:
        return 80


def compute_spectrum(stream: Stream, curr_bass, curr_mid, curr_treble):
    spectrum = get_spectrum(
        stream.mononize(stream.raw_to_float(stream.get())), stream.sample_rate
    )
    # Get spectrum for each of the three ranges
    bass = spectrum[
        (spectrum[:, 0] >= bass_range[0]) & (spectrum[:, 0] <= bass_range[1])
    ]
    mid = spectrum[(spectrum[:, 0] >= mid_range[0]) & (spectrum[:, 0] <= mid_range[1])]
    treble = spectrum[
        (spectrum[:, 0] >= treble_range[0]) & (spectrum[:, 0] <= treble_range[1])
    ]

    # Compute their percents
    bass_percent = compute_percent(
        bass[:, 1],
        use_db=True,
        min_db=bass_db_range[0],
        max_db=bass_db_range[1],
    )
    mid_percent = compute_percent(
        mid[:, 1],
        use_db=True,
        min_db=mid_db_range[0],
        max_db=mid_db_range[1],
    )
    treble_percent = compute_percent(
        treble[:, 1],
        use_db=True,
        min_db=treble_db_range[0],
        max_db=treble_db_range[1],
    )

    # Apply decay
    new_values = (
        apply_decay(curr_bass, bass_percent, decay=decay),
        apply_decay(curr_mid, mid_percent, decay=decay),
        apply_decay(curr_treble, treble_percent, decay=decay),
    )
    return new_values


# def retrieve_lyrics(title, artist):


def main():
    playing = NowPlaying()
    run(playing.initalize_mediamanger())
    playing.get_active_app_user_model_ids
    # Get initial info
    info = run(get_info(playing))
    title = info["title"] if info else "No song playing"
    artist = info["artist"] if info else "Unknown artist"

    # Lyrics
    lyric_to_display = ""
    if display_lyrics:
        lyrics = Lyrics(title, "")
        lyrics.retrieve()

    # Get thumbnail
    thumbnail_url = fetch_thumbnail(title, info["player"])
    save_thumbnail(thumbnail_url, "thumbnail.png")
    ascii_image = AsciiImage("thumbnail.png")
    # return
    # Initialize audio stream
    stream = Stream()
    curr_bass = 0
    curr_mid = 0
    curr_treble = 0

    # new_info_freq in Frames. Smaller value = more frequent updates, but more potential stutters
    # Also note that the higher this is set, the more lag there before song_start is updated
    new_info_freq = 0
    frames_passed = 0
    song_start = time()
    curr_time = 0

    # clear terminal
    # return
    print("\033c", end="")

    try:
        while True:
            # Get Info
            frames_passed += 1
            if frames_passed >= new_info_freq:
                frames_passed = 0
                info = run(get_info(playing))
            new_title = info["title"] if info else "No song playing"
            artist = info["artist"] if info else "Unknown artist"

            # Update thumbnail if title changed
            if new_title != title:
                title = new_title
                song_start = time()
                curr_time = 0
                thumbnail_url = fetch_thumbnail(title, info["player"])
                save_thumbnail(thumbnail_url, "thumbnail.png")
                if display_lyrics:
                    lyric_to_display = ""
                    lyrics = Lyrics(title, "")
                    lyrics.retrieve()
                print("\033c", end="")
            # Process audio

            curr_bass, curr_mid, curr_treble = compute_spectrum(
                stream,
                curr_bass,
                curr_mid,
                curr_treble,
            )

            curr_time = time()

            # Get lyrics
            if display_lyrics:
                lyric_time = int(curr_time - song_start)
                if lyrics.get_lyric(lyric_time):
                    lyric_to_display = lyrics.get_lyric(lyric_time)

            # Display
            if ascii_art:
                for line in ascii_image.ascii_image_str(
                    ascii_size, ascii_square, colored=colored_ascii
                ):
                    print(line, end="")

            print("-" * get_console_width())
            print(f"{title} - {artist}".ljust(get_console_width()))
            print("-" * get_console_width())
            if display_lyrics:
                print(f"Lyrics: {lyric_to_display}".ljust(get_console_width()))
                print("-" * get_console_width())
            update_bars(curr_bass * 100, curr_mid * 100, curr_treble * 100)
            print(f"\x1b[{ascii_size}A", end="")  # Move cursor up to redraw
            print(f"\x1b[{ascii_size}A", end="")  # Move cursor up to redraw

    except KeyboardInterrupt:
        stream.terminate()
        print("\033c", end="")
        return

    # except Exception as e:
    #     stream.terminate()
    #     print("\033c", end="")
    #     print("Error:", str(e).ljust(80))
    #     return


if __name__ == "__main__":
    main()
