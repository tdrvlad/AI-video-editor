import os
from typing import List, Tuple

from objects.media_clip import MediaClip, concatenate_media_clips
from objects.media_segment import MediaSegment, save_media_segment, SEGMENTS_META_DIR_NAME, SEGMENTS_DIR_NAME

from utils import clear_and_create_dir


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


def paste_media_segments(
    media_segments: List[MediaSegment],
    output_path: str,
    start_trim: float = 0.0,
    end_trim: float = 0.0,
    transition='crossFadeIn',
    transition_duration: float = 0.2,
    use_subbed: bool = False
) -> None:
    media_clips = []

    # Load each media segment as a MediaClip, and trim according to start/end margin
    for segment in media_segments:
        if segment.subbed_media_file_path is None:
            print(f'Missing subbed media {segment.subbed_media_file_path}.')
            continue  # Skip if the subbed path is missing

        if use_subbed:
            media_clip = MediaClip(file_path=segment.subbed_media_file_path)
        else:
            media_clip = MediaClip(file_path=segment.media_file_path)
        clip_duration = media_clip.clip.duration

        # Determine start and end times for subclipping with trims
        start_time = max(0.0, start_trim)
        end_time = max(0.0, clip_duration - end_trim)

        if start_time >= end_time:
            print(f"Warning: Start trim ({start_time}) is beyond or equal to end trim ({end_time}) for clip '{segment.file_path}'. Skipping this clip.")
            media_clip.close()
            continue

        trimmed_clip = media_clip.subclip(start_time, end_time)
        media_clips.append(trimmed_clip)

    # Ensure we have media clips to stitch
    if not media_clips:
        raise ValueError("No media segments found to stitch together.")

    result_media_clip = concatenate_media_clips(media_clips, transition=transition, transition_duration=transition_duration)

    result_media_clip.write(output_path)
    for media_clip in media_clips:
        media_clip.close()
    result_media_clip.close()
