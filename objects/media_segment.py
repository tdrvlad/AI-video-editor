import json
from typing import Optional
import glob
from pydantic import BaseModel
import os
from typing import List
from objects.transcription import Transcription

SOURCE_VIDEOS_DIR = os.getenv("SOURCE_VIDEOS_DIR")
RESULT_VIDEOS_DIR = os.getenv("RESULT_VIDEOS_DIR")

SEGMENTS_META_DIR_NAME = "segments_meta"
SEGMENTS_DIR_NAME = "segments"
SUBBED_SEGMENTS_DIR_NAME = "subbed_segments"


class MediaSegment(BaseModel):
    timestamp_start: float
    timestamp_end: float
    language: Optional[str] = None
    transcription_uuid: Optional[str] = None
    transcription: Optional[Transcription] = None
    corrected_transcription: Optional[Transcription] = None
    text: Optional[str] = None
    corrected_text: Optional[str] = None
    grammar_is_checked: bool = False
    grammar_is_checked_manual: bool = False
    file_path: str
    media_file_path: str
    subbed_media_file_path: Optional[str]
    removed: Optional[bool] = False

    def to_dict(self):
        """
        Convert the MediaSegment instance to a dictionary, including nested objects.
        """
        return self.dict()

    @classmethod
    def from_dict(cls, data):
        """
        Create a MediaSegment instance from a dictionary.
        """
        return cls(**data)


def save_media_segment(media_segment: MediaSegment, file_path: Optional[str] = None):
    if file_path is None:
        if media_segment.file_path is None:
            raise Exception("No path for MediaSegment meta file provided.")
        file_path = media_segment.file_path
    with open(file_path, 'w') as f:
        json.dump(media_segment.to_dict(), f, indent=4)


def load_media_segment(file_path) -> MediaSegment:
    with open(file_path, 'r') as f:
        data = json.load(f)
        return MediaSegment.from_dict(data)


def load_media_segments(file_name: str) -> List[MediaSegment]:
    segments_meta_dir = os.path.join(RESULT_VIDEOS_DIR, file_name, SEGMENTS_META_DIR_NAME)
    segments_meta_files = glob.glob(os.path.join(segments_meta_dir, "*.json"))
    segments_meta = [load_media_segment(f) for f in segments_meta_files]
    print(f"Found meta for {len(segments_meta)} segments.")

    # If the media was removed, it means that it was decided it is not to be used so we discard it.
    filtered_segments_meta = [meta for meta in segments_meta if os.path.exists(meta.media_file_path)]
    print(f"{len(segments_meta) - len(filtered_segments_meta)} segments have been removed.")

    ordered_segments_meta = sorted(filtered_segments_meta, key=lambda x: x.timestamp_start)
    return ordered_segments_meta

