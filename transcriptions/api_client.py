import os
import dotenv
from typing import List, Tuple, Optional
import json
import requests
from objects.media_archive import MediaArchive, Media
import time

from objects.transcription import TranscribedWord, Transcription
from objects.language import Language, transcription_language_dict

dotenv.load_dotenv()

API_KEY = os.getenv("VATIS_API_KEY")
POST_FILE_URL = "https://vatis.tech/api/v1/files/transcribe/file"
GET_TRANSCRIPT_URL = "https://vatis.tech/api/v1/transcripts/"


class TranscriptClient:
    post_file_url = POST_FILE_URL
    get_transcript_url = GET_TRANSCRIPT_URL
    not_transcripted = "NOT_TRANSCRIPTED"
    transcripted = "TRANSCRIPTED"
    queued = "QUEUED"
    trasncripting = "TRANSCRIPTING"

    def __init__(self, api_key: str = API_KEY):
        self.media_archive = MediaArchive()
        self.api_key = api_key

    def submit(self, file_path: str, language: str = Language.romanian) -> str:
        """Trigger the transcription process for the uploaded file."""
        print("Sending media for transcription.")

        payload = {
            'language': transcription_language_dict.get(language),
            'transcribe': True
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb'))
        }
        response = requests.post(
            url=self.post_file_url,
            headers=headers,
            data=payload,
            files=files
        )
        if response.status_code != 200:
            raise Exception("Failed to start transcription:", response.text)

        data = json.loads(response.text)
        transcription_uid = data["uid"]
        return transcription_uid

    def get_transcription(self, transcription_uuid: str) -> Tuple[str, Transcription]:
        url = f"{self.get_transcript_url}{transcription_uuid}"
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception("Failed to check transcription status:", response.text)
        data = response.json()
        state = data['status']
        if state != self.transcripted:
            return state, Transcription(words=[])
        transcript = Transcription(
            words=process_transcript(data['data']['words'])
        )
        return state, transcript

    def get_transcription_with_wait(self, transcription_uuid: str, max_wait: int = 50) -> Optional[Transcription]:
        start_time = time.time()
        state, transcript = self.get_transcription(transcription_uuid)

        while state != self.transcripted and time.time() - start_time < max_wait:
            print(f"Transcription in state {state}. Waiting...")
            time.sleep(10)
            state, transcript = self.get_transcription(transcription_uuid)

        if state == self.transcripted:
            print(f"Transcription finished and successful.")
            return transcript

        raise Exception(f"Transcription is not yet ready from Service API - state: {state}")


def process_transcript(transcript: List[dict]) -> List[TranscribedWord]:
    transcribed_words = [
        TranscribedWord(
            start=word_dict["startTime"],
            end=word_dict["endTime"],
            word=word_dict["word"]
        )
        for word_dict in transcript
    ]
    return transcribed_words
