import librosa
import numpy as np
from moviepy import *
from PIL import Image, ImageOps
import os
import pillow_heif
import tempfile

pillow_heif.register_heif_opener()

def load_rgb_image(path):
    """
    Loads an image from the specified path, applies EXIF orientation correction,
    converts it to RGB, and returns it as a NumPy array.

    Args:
        path (str): Path to the image file.

    Returns:
        np.ndarray: RGB image as NumPy array.
    """
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        return np.array(img)

def generate_slideshow(audio_path, image_folder, output_video="slideshow.mp4", sort_by="name"):
    """
    Generates a video slideshow from images synced with beats detected in the audio file.

    Args:
        audio_path (str): Path to the audio file.
        image_folder (str): Folder containing the image files.
        output_video (str, optional): Path to the final output video. Defaults to "slideshow.mp4".
        sort_by (str, optional): Sorting mode for image files. One of:
            "name", "created_asc", "created_desc", "modified_asc", "modified_desc".

    Raises:
        Exception: If no valid images are found.
    """
    y, sr = librosa.load(audio_path, sr=None)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    def get_sort_key(path):
        full_path = os.path.join(image_folder, path)
        if sort_by == "name":
            return path.lower()
        elif sort_by == "created_asc":
            return os.path.getctime(full_path)
        elif sort_by == "created_desc":
            return -os.path.getctime(full_path)
        elif sort_by == "modified_asc":
            return os.path.getmtime(full_path)
        elif sort_by == "modified_desc":
            return -os.path.getmtime(full_path)
        else:
            raise ValueError(f"Invalid sort_by value: {sort_by}")

    files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.heic'))]
    sorted_files = sorted(files, key=get_sort_key)

    valid_images = []
    for f in sorted_files:
        path = os.path.join(image_folder, f)
        try:
            with Image.open(path) as img:
                img.load()
            valid_images.append(path)
        except Exception as e:
            print(f"⚠️ Skipped broken image: {f} ({e})")

    if not valid_images:
        raise Exception("No valid images found!")
    print(f"Best times count: {len(beat_times)}")
    clips = []
    for i, start in enumerate(beat_times):
        end = beat_times[i+1] if i+1 < len(beat_times) else beat_times[i] + 1
        duration = end - start
        img_path = valid_images[i % len(valid_images)]
        clip = (
            ImageClip(load_rgb_image(img_path))
            .with_duration(duration)
            .resized(height=720)
            .resized(width=min(1920, Image.open(img_path).width))
        )
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio_clip = AudioFileClip(audio_path)
    safe_duration = min(video.duration, audio_clip.duration)
    audio = audio_clip.subclipped(0, safe_duration)
    final = video.with_audio(audio)
    final.write_videofile(output_video, fps=24)


def generate_slideshow_video(audio_path, media_folder, output_video="slideshow.mp4", sort_by="name"):
    """
    Generates a memory-efficient video slideshow from images and videos,
    synchronized to audio beats using temporary files and ffmpeg concat.

    Args:
        audio_path (str): Path to the audio file.
        media_folder (str): Folder containing images/videos.
        output_video (str, optional): Output file path. Defaults to "slideshow.mp4".
        sort_by (str, optional): Sorting mode for media files. One of:
            "name", "created_asc", "created_desc", "modified_asc", "modified_desc".

    Raises:
        Exception: If no valid media files are found.
    """
    y, sr = librosa.load(audio_path, sr=None)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    def get_sort_key(path):
        full_path = os.path.join(media_folder, path)
        if sort_by == "name":
            return path.lower()
        elif sort_by == "created_asc":
            return os.path.getctime(full_path)
        elif sort_by == "created_desc":
            return -os.path.getctime(full_path)
        elif sort_by == "modified_asc":
            return os.path.getmtime(full_path)
        elif sort_by == "modified_desc":
            return -os.path.getmtime(full_path)
        else:
            raise ValueError(f"Invalid sort_by value: {sort_by}")

    supported_images = ('.png', '.jpg', '.jpeg', '.heic')
    supported_videos = ('.mp4', '.mov', '.avi', '.webm', '.mkv')
    files = [f for f in os.listdir(media_folder) if f.lower().endswith(supported_images + supported_videos)]
    sorted_files = sorted(files, key=get_sort_key)

    if not sorted_files:
        raise Exception("No valid media files found!")

    print(f"Beat times count: {len(beat_times)}")

    temp_dir = tempfile.mkdtemp()
    temp_files = []

    for i, start in enumerate(beat_times):
        end = beat_times[i+1] if i+1 < len(beat_times) else beat_times[i] + 1
        duration = end - start
        path = os.path.join(media_folder, sorted_files[i % len(sorted_files)])
        ext = os.path.splitext(path)[1].lower()

        try:
            if ext in supported_images:
                clip = ImageClip(path).with_duration(duration).resized(height=720)
            elif ext in supported_videos:
                video = VideoFileClip(path)
                subclip_duration = min(duration, video.duration)
                clip = video.subclipped(0, subclip_duration).with_duration(duration).resized(height=720)
            else:
                continue

            temp_path = os.path.join(temp_dir, f"clip_{i:05d}.mp4")
            clip.write_videofile(temp_path, fps=24, audio=False, codec="libx264", logger=None)
            temp_files.append(temp_path)
            clip.close()
            if ext in supported_videos:
                video.close()

        except Exception as e:
            print(f"⚠️ Skipped {path} due to error: {e}")

    concat_list_path = os.path.join(temp_dir, "concat.txt")
    with open(concat_list_path, "w") as f:
        for file in temp_files:
            f.write(f"file '{file}'\n")

    output_merged = os.path.join(temp_dir, "merged.mp4")
    os.system(f"ffmpeg -y -f concat -safe 0 -i '{concat_list_path}' -c copy '{output_merged}'")

    final = VideoFileClip(output_merged).with_audio(AudioFileClip(audio_path))
    final.write_videofile(output_video, fps=24)