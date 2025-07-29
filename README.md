# beatsynchr
Python library for syncing images and videos with music beats

## 🎵 Features

- Beat-based slideshow generation
- Supports both images and video files
- Handles `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`
- Automatically matches clip duration to beat intervals

---

## Installation

```bash
pip install beatsynchr
```
## Usage

```python
from beatsynchr import generate_slideshow, generate_slideshow_video

# Create slideshow from images
generate_slideshow(
    audio_path="soundtrack.mp3",
    image_folder="./images",
    output_video="slideshow.mp4",
    sort_by="name"  # or created_asc, created_desc, modified_asc, modified_desc
)

# Create slideshow from images + videos
generate_slideshow_video(
    audio_path="soundtrack.mp3",
    media_folder="./media",
    output_video="media_slideshow.mp4",
    sort_by="name"
)
```

## Warning

For handling videos, you must have **ffmpeg** installed and accessible in your system PATH.

---