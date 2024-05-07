import os
from typing import Optional, Union, List

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, CompositeAudioClip
from moviepy.editor import concatenate_videoclips, concatenate_audioclips


class MediaClip:
    def __init__(self, file_path: Optional[str] = None, clip: Optional[Union[VideoFileClip, AudioFileClip]] = None):
        if file_path is not None:
            self.__init_file_path(file_path)
        else:
            self.__init_clip(clip)

    def __init_clip(self, clip: Union[VideoFileClip, AudioFileClip]):
        self.clip = clip
        self.media_type = type(clip)
        if isinstance(clip, VideoFileClip) or isinstance(clip, CompositeVideoClip):
            self.writer_method = 'write_videofile'
            self.codec = {"codec": "libx264"}
        elif isinstance(clip, AudioFileClip) or isinstance(clip, CompositeAudioClip):
            self.writer_method = 'write_audiofile'
            self.codec = {}
        else:
            raise ValueError("Unsupported clip type")

    def __init_file_path(self, file_path):
        self.file_path = file_path
        file_name = os.path.basename(file_path)
        extension = os.path.splitext(file_name)[1].lower()
        if extension in ['.mp4', '.mov', '.avi']:
            self.media_type = VideoFileClip
            self.writer_method = 'write_videofile'
            self.codec = {"codec": "libx264"}
        elif extension in ['.mp3', '.wav', '.aac']:
            self.media_type = AudioFileClip
            self.writer_method = 'write_audiofile'
            self.codec = {}
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        self.clip = self.media_type(self.file_path)
        self.duration = self.clip.duration

    def subclip(self, start_timestamp: float, end_timestamp: float):
        clip = self.clip.subclip(start_timestamp, end_timestamp)
        return MediaClip(clip=clip)

    def close(self):
        self.clip.close()

    def write(self, file_path):
        writer = getattr(self.clip, self.writer_method)
        writer(file_path, **self.codec)

    def preview_audio(self):
        self.clip.audio.preview()


def concatenate_media_clips(media_clips: List[MediaClip], transition='crossFadeIn', transition_duration: float = 0.2) -> MediaClip:

    clips = [media_clip.clip for media_clip in media_clips]
    if all([media_clip.media_type == VideoFileClip for media_clip in media_clips]):
        if transition == 'crossFadeIn':
            clips = [clip.crossfadein(transition_duration).crossfadeout(transition_duration) for clip in clips]

        final_clip = concatenate_videoclips(
            clips=clips,
            method='compose'
        )
    elif all([media_clip.media_type == AudioFileClip for media_clip in media_clips]):
        final_clip = concatenate_audioclips(
            clips=clips
        )
    else:
        raise ValueError("Unsupported media type for stitching.")

    result_media_clip = MediaClip(clip=final_clip)
    return result_media_clip
