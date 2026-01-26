import pyaudiowpatch as pyaudio
import threading
import numpy as np


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


def get_spectrum(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """
    Retrieves the frequency spectrum of the given audio data using FFT.

    :param audio: The audio data as a numpy array.
    :type audio: np.ndarray
    :param sample_rate: The sample rate of the audio data.
    :type sample_rate: int
    """
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
