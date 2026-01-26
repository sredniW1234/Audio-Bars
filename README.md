# Audio Bars

A Python application that displays now playing information with real-time audio spectrum visualization and ASCII art album thumbnails.

## Features

- **Real-time Audio Visualization**: Displays bass, mid, and treble frequency bars
- **ASCII Art Thumbnails**: Converts album artwork to colored ASCII art
- **Now Playing Info**: Shows current song title and artist
- **Spectrum Analysis**: Uses FFT to analyze audio frequencies
- **Smooth Decay**: Implements audio bar decay for smooth visual transitions

## Requirements

- Windows OS (requires WASAPI support)
- Python 3.8+
- Dependencies: `pyaudiowpatch`, `numpy`, `yt-dlp`, `pillow`, `colorama`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/sredniW1234/Audio-Bars.git
cd audio-bars
```

### 2. Install Dependencies

#### Option A: Using uv (Recommended)

```bash
uv pip install pyaudiowpatch numpy yt-dlp pillow colorama
```

#### Option B: Using pip with requirements.txt

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Press `Ctrl+C` to exit.

## Notes

- Windows only (WASAPI loopback required)
- Only one Stream instance should be created to avoid conflicts
- Supports browser-based media players (Chrome, Firefox, Edge, Opera, Brave)

## Acknowledgments

This project was developed with the assistance of AI, including code generation and optimization. However, a majority of it was created by the creator: Winders.

