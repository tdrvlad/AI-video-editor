import os
import dotenv
import json
from typing import Optional, List, Tuple
from pydantic import BaseModel
from transcriptions.objects import Transcription

dotenv.load_dotenv()

API_KEY = os.getenv("VATIS_API_KEY")
CACHE_FILE = os.getenv("CACHE_FILE")


class Media(BaseModel):
    file_path: str
    transcription_uuid: str
    language: str
    transcription: Optional[Transcription] = None
    corrected_transcription: Optional[Transcription] = None
    speech_segments: Optional[List[Tuple[float, float]]] = None
    pause_segments: Optional[List[Tuple[float, float]]] = None
    repetition_segments: Optional[List[Tuple[float, float]]] = None


class MediaArchive:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self.load()

    def load(self):
        if not os.path.exists(self.cache_file):
            return {}
        with open(self.cache_file, 'r') as file:
            data = json.load(file)
        cache = {key: Media.parse_obj(value) for key, value in data.items()}
        return cache

    def save(self):
        serializable_cache = {key: value.dict() for key, value in self.cache.items()}
        with open(self.cache_file, 'w') as file:
            json.dump(serializable_cache, file, indent=4)

    def add_media(self, media: Media):
        self.cache[media.file_path] = media
        self.save()

    def get_media(self, file_path: str) -> Optional[Media]:
        media = self.cache.get(file_path, None)
        return media

    def media_exists(self, file_path: str) -> bool:
        return self.get_media(file_path) is not None

    def add_transcript_to_media(self, transcription: Transcription, file_path: str):
        media = self.get_media(file_path)
        if media is None:
            raise Exception(f"Media {os.path.basename(file_path)} does not exist in cache.")
        media.transcription = transcription

