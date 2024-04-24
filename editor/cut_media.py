import os
from typing import List, Tuple

from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip


def cut_media(file_path: str, output_dir_path: str, cuts: List[Tuple[float, float]], save_cuts: bool = True):

    file_name = os.path.basename(file_path)
    extension = os.path.splitext(file_name)[1].lower()

    if extension in ['.mp4', '.mov', '.avi']:
        return cut_video(
            file_path=file_path,
            output_dir_path=output_dir_path,
            cuts=cuts,
            save_cuts=save_cuts
        )

    elif extension in ['.mp3', '.wav', '.aac']:
        return cut_audio(
            file_path=file_path,
            output_dir_path=output_dir_path,
            cuts=cuts,
            save_cuts=save_cuts
        )
    else:
        raise ValueError(f"Unsupported file type: {extension}")


def cut_audio(file_path: str, output_dir_path: str, cuts: List[Tuple[float, float]], save_cuts: bool = True):
    # Load the audio file using AudioFileClip
    audio = AudioFileClip(file_path)
    file_name = os.path.basename(file_path)

    result_audio_filename = f"cut_{file_name}"
    result_audio_file_path = os.path.join(output_dir_path, result_audio_filename)

    # Directory to store the individual cuts, if save_cuts is True
    cuts_dir = os.path.join(output_dir_path, "cuts")
    os.makedirs(cuts_dir, exist_ok=True)

    audio_cuts = []
    last_end = 0
    for start, end in sorted(cuts):
        if start > last_end:
            audio_cuts.append(audio.subclip(last_end, start))
        last_end = end
    if last_end < audio.duration:
        audio_cuts.append(audio.subclip(last_end, audio.duration))

    if save_cuts:
        for i, clip in enumerate(audio_cuts):
            cut_file_path = os.path.join(cuts_dir, f"{i}_{file_name}")
            clip.write_audiofile(cut_file_path)
    else:
        result_audio = concatenate_audioclips(audio_cuts)
        result_audio.write_audiofile(result_audio_file_path)
        result_audio.close()

    audio.close()
    for clip in audio_cuts:
        clip.close()

    return result_audio_file_path


def cut_video(file_path: str, output_dir_path: str, cuts: List[Tuple[float, float]], save_cuts: bool = True):

    video = VideoFileClip(file_path)
    file_name = os.path.basename(file_path)

    result_video_filename = f"cut_{file_name}"
    result_video_file_path = os.path.join(output_dir_path, result_video_filename)

    cuts_dir = os.path.join(output_dir_path, "cuts")
    os.makedirs(cuts_dir, exist_ok=True)

    video_cuts = []
    last_end = 0
    for start, end in sorted(cuts):
        if start > last_end:
            video_cuts.append(video.subclip(last_end, start))
        last_end = end
    if last_end < video.duration:
        video_cuts.append(video.subclip(last_end, video.duration))

    if save_cuts:
        for i, clip in enumerate(video_cuts):
            clip.write_videofile(os.path.join(cuts_dir, f"{i}_{file_name}"), codec="libx264")
    else:
        result_video = concatenate_videoclips(video_cuts)
        result_video.write_videofile(result_video_file_path, codec="libx264")
        result_video.close()

    video.close()
    for clip in video_cuts:
        clip.close()

    return result_video_file_path