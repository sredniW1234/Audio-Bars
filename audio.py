import pyaudiowpatch as pyaudio
import numpy as np
import threading
import rapidfuzz
import yt_dlp
import os


class Stream:
    def __init__(self) -> None:
        """
        A Audio stream class to capture system audio using WASAPI loopback.
        Note: This only works on Windows with WASAPI support.
        Note: Only one instance of this class should be created to avoid conflicts.
        """

        self.frames = []

        if pyaudio.paNotInitialized:
            self.p = pyaudio.PyAudio()

        self.loopback_info = self.p.get_default_wasapi_loopback()
        self.sample_rate = self.loopback_info["defaultSampleRate"]
        self.channels = self.loopback_info["maxInputChannels"]
        # print("Using loopback device:", self.loopback_info["name"])

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=int(self.sample_rate),
            input=True,
            frames_per_buffer=1024,
            input_device_index=self.loopback_info["index"],
        )

        self.lock = threading.Lock()
        self.start()

    def start(self):
        """
        Starts the audio stream in a separate thread. Automatically called on initialization.
        """

        def listen():
            try:
                while True:
                    with self.lock:
                        data = self.stream.read(1024)
                        self.frames.append(data)
            except Exception as e:
                print("Error in audio stream:", e)
                self.terminate()

        # print("Listening...")
        self.thread = threading.Thread(target=listen)
        self.thread.start()

    def get(self) -> list[bytes]:
        """
        Retrieves and clears the captured audio frames.

        :return: List of raw audio frames as bytes.
        :rtype: list[bytes]
        """
        # print("Retrieving...")
        with self.lock:
            audio_frames = self.frames.copy()
            self.frames = []
        return audio_frames

    def _bytes_to_float32(self, data: bytes, channels: int) -> np.ndarray:
        # Convert raw bytes to int16
        samples = np.frombuffer(data, dtype=np.int16)

        # Normalize to [-1, 1]
        samples = samples.astype(np.float32) / 32768.0

        # De-interleave channels
        samples = samples.reshape(-1, channels)

        return samples

    def raw_to_float(self, data: list[bytes]) -> np.ndarray:
        """
        Converts raw audio byte data to a numpy array of float32 samples.

        :param data: The raw audio data as a list of byte strings.
        :type data: list[bytes]
        :return: Numpy array of float32 audio samples.
        :rtype: NDArray[Any]
        """
        audio_frames = []
        for chunk in data:
            audio_frames.append(
                self._bytes_to_float32(chunk, self.loopback_info["maxInputChannels"])
            )
        return np.array(audio_frames)

    def mononize(self, audio: np.ndarray) -> np.ndarray:
        """
        Turns multi-channel audio into mono by averaging the channels.

        :param audio: The audio data as a numpy array.
        :type audio: np.ndarray
        """
        if audio.size == 0:
            return audio
        audio = audio.reshape(-1, audio.shape[-1])
        # Get mono
        audio = np.mean(audio, axis=1)
        return audio

    def terminate(self):
        """
        Terminates the audio stream and releases resources.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class BandSetting:
    def __init__(
        self,
        freq_range: tuple[int, int],
        db_range: tuple[int, int] = (-40, 40),
    ) -> None:
        self.curr: float = 0
        self.low_freq = freq_range[0]
        self.high_freq = freq_range[1]
        self.low_db = db_range[0]
        self.high_db = db_range[1]


def get_spectrum(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """
    Retrieves the frequency spectrum of the given audio data using FFT.

    :param audio: The audio data as a numpy array.
    :type audio: np.ndarray
    :param sample_rate: The sample rate of the audio data.
    :type sample_rate: int
    """
    if audio.size == 0:
        return np.array([])
    # Apply Hanning window
    window = np.hanning(len(audio))
    windowed = audio * window

    # Perform FFT
    fft = np.fft.rfft(windowed)
    magnitude = np.abs(fft)

    # Get frequency bins
    freqs = np.fft.rfftfreq(len(windowed), d=1 / sample_rate)

    spectrum = np.column_stack((freqs, magnitude))
    return spectrum


def compute_percent(band_magnitudes: np.ndarray, min_db=-40, max_db=0) -> float:
    avg_mag = np.mean(band_magnitudes)
    eps = 1e-10
    db: float = 20 * np.log10(avg_mag + eps)
    percent = (db - min_db) / (max_db - min_db)
    return np.clip(percent, 0, 1)


def volume_db(samples: np.ndarray, min_db=-40, max_db=0) -> float:
    rms = np.sqrt(np.mean(samples**2))  # AI
    eps = 1e-10
    db = 20 * np.log10(rms + eps)
    percent = (db - min_db) / (max_db - min_db)
    return np.clip(percent, 0, 1)


def apply_decay(prev, current: float, decay=0.05) -> float:
    if current >= prev:
        # rising signal: jump instantly
        return current
    else:
        # falling signal: decay gradually
        return prev * (1 - decay) + current * decay


def compute_spectrum(
    stream: Stream,
    bass_setting: BandSetting,
    mid_setting: BandSetting,
    treble_setting: BandSetting,
    volume_setting: BandSetting,
    decay: float = 0.1,
):
    audio = stream.mononize(stream.raw_to_float(stream.get()))
    spectrum = get_spectrum(audio, stream.sample_rate)
    # Get spectrum for each of the three ranges
    bass = spectrum[
        (spectrum[:, 0] >= bass_setting.low_freq)
        & (spectrum[:, 0] <= bass_setting.high_freq)
    ]
    mid = spectrum[
        (spectrum[:, 0] >= mid_setting.low_freq)
        & (spectrum[:, 0] <= mid_setting.high_freq)
    ]
    treble = spectrum[
        (spectrum[:, 0] >= treble_setting.low_freq)
        & (spectrum[:, 0] <= treble_setting.high_freq)
    ]

    # Compute their percents
    bass_percent = compute_percent(
        bass[:, 1],
        bass_setting.low_db,
        bass_setting.high_db,
    )
    mid_percent = compute_percent(
        mid[:, 1],
        mid_setting.low_db,
        mid_setting.high_db,
    )
    treble_percent = compute_percent(
        treble[:, 1],
        treble_setting.low_db,
        treble_setting.high_db,
    )
    volume_percent = volume_db(
        audio,
        volume_setting.low_db,
        volume_setting.high_db,
    )

    # Apply decay
    new_values = (
        apply_decay(bass_setting.curr, bass_percent, decay=decay),
        apply_decay(mid_setting.curr, mid_percent, decay=decay),
        apply_decay(treble_setting.curr, treble_percent, decay=decay),
        apply_decay(volume_setting.curr, volume_percent, decay=decay),
    )
    return new_values


# def download_vid(title):
#     ydl_opts = {
#         "format": "bestaudio/best",  # downloads best video and audio and merges them
#         "outtmpl": os.path.join(
#             "./", "audio"
#         ),  # output template: "downloads/Video Title.ext"
#         "noplaylist": True,  # ensures only the single video is downloaded if a playlist URL is provided
#         "quiet": True,
#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio",  # Key for audio extraction
#                 "preferredcodec": "mp3",  # Preferred output format (mp3, wav, aac, etc.)
#                 "preferredquality": "192",  # Audio quality (64 to 320)
#             }
#         ],
#     }
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type:ignore
#             info = ydl.extract_info(f"ytsearch1:{title}", download=False)
#             info = info["entries"][0]  # type:ignore
#             if (
#                 1 - rapidfuzz.distance.DamerauLevenshtein.distance(title, info["title"])
#                 > 0.85
#             ):
#                 ydl.download(info["webpage_url"])
#         # print(f"\nSuccessfully downloaded: {video_url}")
#     except Exception as e:
#         print(f"\nAn error occurred: {e}")
