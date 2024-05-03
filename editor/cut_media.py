import os
import shutil
from typing import List, Tuple, Optional, Union

from objects.media_segment import MediaSegment, save_media_segment, SEGMENTS_META_DIR_NAME, SEGMENTS_DIR_NAME
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip


def clear_and_create_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)


class MediaClip:
    def __init__(self, file_path: Optional[str] = None, clip: Optional[Union[VideoFileClip, AudioFileClip]] = None):
        if file_path is not None:
            self.__init_file_path(file_path)
        else:
            self.__init_clip(clip)

    def __init_clip(self, clip: Union[VideoFileClip, AudioFileClip]):
        self.clip = clip
        self.media_type = type(clip)
        if isinstance(clip, VideoFileClip):
            self.writer_method = 'write_videofile'
            self.codec = {"codec": "libx264"}
        elif isinstance(clip, AudioFileClip):
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


def cut_media(file_path: str, output_dir_path: str, segments_to_keep: List[Tuple[float, float]]):
    file_name = os.path.basename(file_path)
    print(f"Cutting media {file_name}")

    media_clip = MediaClip(file_path)

    segments_dir = os.path.join(output_dir_path, SEGMENTS_DIR_NAME)
    segments_meta_dir = os.path.join(output_dir_path, SEGMENTS_META_DIR_NAME)

    clear_and_create_dir(segments_dir)
    clear_and_create_dir(segments_meta_dir)

    media_segments = []
    segment_clips = []

    for i, (segment_start, segment_end) in enumerate(sorted(segments_to_keep)):
        segment_path = os.path.join(segments_dir, f"{int(segment_start)}-{int(segment_end)}-{file_name}")
        segment_meta_path = os.path.join(segments_meta_dir, f"{int(segment_start)}-{int(segment_end)}-{file_name}.json")

        segment_clip = media_clip.subclip(
            start_timestamp=max(0.0, segment_start),
            end_timestamp=min(segment_end, media_clip.duration)
        )
        segment_clip.write(segment_path)
        segment_clips.append(segment_clip)

        media_segment = MediaSegment(
            timestamp_start=segment_start,
            timestamp_end=segment_end,
            file_path=segment_meta_path,
            media_file_path=segment_path
        )

        media_segments.append(media_segment)
        save_media_segment(media_segment, segment_meta_path)

    media_clip.close()
    [segment_clip.close() for segment_clip in segment_clips]
    return media_segments
