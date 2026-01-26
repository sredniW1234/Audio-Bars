from thumbnail import fetch_thumbnail, save_thumbnail
from winnplib import get_media_info_async
from audio import Stream, get_spectrum
from bar import Bar, MultiBar
from ascii import AsciiImage
from asyncio import run
import numpy as np

"""
Main application to display now playing info with audio bars and ASCII art thumbnail.
Note: Requires Windows OS.
Note: Some code was generated with the help of ChatGPT. Though I have modified it, I acknowledge its assistance.
"""

# TODO: Improve ASCII art aspect ratio handling
# TODO: Don't download thumbnail and only get the PIL image in memory
# TODO: Add volume bar
# TODO: Fine tune db_range settings
# TODO: Add command line arguments for settings
# TODO: Make bars more visually appealing
# TODO: Make Title print more pretty

# Some simple Settings:
# Bars:
bar_total_length: int = 40  # Characters

# Spectrum:
bass_range: tuple = (20, 250)  # freq in hz
mid_range: tuple = (200, 4500)
treble_range: tuple = (4000, 20000)

bass_db_range: tuple = (-40, 40)  # minimum, maximum
mid_db_range: tuple = (-40, 40)
treble_db_range: tuple = (-40, 20)

decay: float = 0.4  # Lower == slower decay

# Ascii:
ascii_size: int = 60
ascii_square: bool = False  # Doesn't look quiet correct yet, but square enough /shrug


def update_bars(bass, mid, treble):
    bass_bar = Bar("Bass", bar_total_length, 8, True)
    mid_bar = Bar("Mid ", bar_total_length, 8, True)
    treble_bar = Bar("Treble", bar_total_length, 8, True)

    bar = MultiBar([bass_bar, mid_bar, treble_bar])
    bar.show([bass, mid, treble])


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


def main():
    # Get initial info
    info = run(get_media_info_async())
    title = info["title"] if info else "No song playing"
    artist = info["artist"] if info else "Unknown artist"

    # Get thumbnail
    thumbnail_url = fetch_thumbnail(title, info["player"])
    save_thumbnail(thumbnail_url, "thumbnail.png")
    ascii_image = AsciiImage("thumbnail.png")

    # Initialize audio stream
    stream = Stream()
    curr_bass = 0
    curr_mid = 0
    curr_treble = 0

    # clear terminal
    print("\033c", end="")

    try:
        while True:
            # Get Info
            info = run(get_media_info_async())
            new_title = info["title"] if info else "No song playing"
            artist = info["artist"] if info else "Unknown artist"

            # Update thumbnail if title changed
            if new_title != title:
                title = new_title
                thumbnail_url = fetch_thumbnail(title, info["player"])
                save_thumbnail(thumbnail_url, "thumbnail.png")
                print("\033c", end="")

            # Process audio
            spectrum = get_spectrum(
                stream.mononize(stream.raw_to_float(stream.get())), stream.sample_rate
            )

            # Get spectrum for each of the three ranges
            bass = spectrum[
                (spectrum[:, 0] >= bass_range[0]) & (spectrum[:, 0] <= bass_range[1])
            ]
            mid = spectrum[
                (spectrum[:, 0] >= mid_range[0]) & (spectrum[:, 0] <= mid_range[1])
            ]
            treble = spectrum[
                (spectrum[:, 0] >= treble_range[0])
                & (spectrum[:, 0] <= treble_range[1])
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
            curr_bass = apply_decay(curr_bass, bass_percent, decay=decay)
            curr_mid = apply_decay(curr_mid, mid_percent, decay=decay)
            curr_treble = apply_decay(curr_treble, treble_percent, decay=decay)

            # Display
            for line in ascii_image.ascii_image_str(ascii_size, ascii_square):
                print(line, end="")
            print(f"{title} - {artist}".ljust(80))
            update_bars(curr_bass * 100, curr_mid * 100, curr_treble * 100)
            print(f"\x1b[{ascii_size}A", end="")  # Move cursor up to redraw
            print(f"\x1b[{ascii_size}A", end="")  # Move cursor up to redraw

    except KeyboardInterrupt:
        stream.terminate()
        print("\033c", end="")
        return

    except Exception as e:
        stream.terminate()
        print("Error:", str(e).ljust(80))
        return


if __name__ == "__main__":
    main()
