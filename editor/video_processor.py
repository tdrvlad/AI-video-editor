from editor.cut_media import cut_video
from editor.subtitles import add_subtitles_to_frames
from editor.cut_media import cut_media
from editor.video_segments_processing import merge_overlapping_cuts, sync_transcription_to_pauses
from transcriptions.transcript import merge_transcript_words
from transcriptions.text_processing import process_special_characters
from typing import List, Tuple
from transcriptions import transcriptor
from transcriptions.api_client import TranscriptClient
from media_archive import archive
from media_archive.media_archive import MediaArchive
from transcriptions.objects import Language, Transcription
from voice_segmentation import detector
from voice_segmentation.voice_activity_detection import VoiceDetector
from moviepy.editor import VideoFileClip
from llm.calls import find_repetitions_timestamps, correct_transcription
import os
import dotenv

dotenv.load_dotenv()

SOURCE_VIDEOS_DIR = os.getenv("SOURCE_VIDEOS_DIR")
RESULT_VIDEOS_DIR = os.getenv("RESULT_VIDEOS_DIR")


def add_subtitles_to_video(file_path: str, output_dir_path: str, transcription: Transcription):
    video = VideoFileClip(file_path)
    file_name = os.path.basename(file_path)

    result_video_filename = f"sub_{file_name}"
    result_video_file_path = os.path.join(output_dir_path, result_video_filename)

    result_video = add_subtitles_to_frames(video=video, transcription=transcription)
    result_video.write_videofile(result_video_file_path, codec="libx264")

    result_video.close()
    video.close()

    return result_video_file_path


def process_video(
        file_path: str,
        output_dir_path: str,
        cuts: List[Tuple[float, float]],
        transcription: Transcription,
        save_cuts: bool = True,
        generate_subtitles: bool = True

):

    if not generate_subtitles:
        result_video_path = cut_media(
            file_path=file_path,
            output_dir_path=output_dir_path,
            cuts=cuts,
            save_cuts=save_cuts
        )

    else:
        subbed_video_path = add_subtitles_to_video(
            file_path=file_path,
            output_dir_path=output_dir_path,
            transcription=transcription
        )

        result_video_path = cut_video(
            file_path=subbed_video_path,
            output_dir_path=output_dir_path,
            cuts=cuts,
            save_cuts=save_cuts
        )

    return result_video_path


class VideoProcessor:
    pause_margin: Tuple[float, float] = (0.0, 0.2)

    def __init__(
            self,
            media_archive: MediaArchive = archive,
            voice_detector: VoiceDetector = detector,
            transcript_client: TranscriptClient = transcriptor,
            source_videos_dir: str = SOURCE_VIDEOS_DIR,
            result_videos_dir: str = RESULT_VIDEOS_DIR
    ):
        self.media_archive = media_archive
        self.transcript_client = transcript_client
        self.voice_detector = voice_detector
        self.source_videos_dir = source_videos_dir
        self.result_videos_dir = result_videos_dir

    def process_video(
            self,
            file_name: str,
            language: str = Language.english,
            correct_grammar: bool = True,
            generate_subtitles: bool = True,
            find_repetitions: bool = True,
            save_cuts: bool = False
    ):

        file_path = os.path.join(self.source_videos_dir, file_name)
        result_dir = os.path.join(self.result_videos_dir, file_name.split(".")[0])

        if self.media_archive.media_exists(file_path):
            print("Loading cached media.")
            media = self.media_archive.get_media(file_path)
            assert media.language == language, "Languages mismatch from ached media."
        else:
            print("Uploading media to Transcriptions API.")
            media = self.transcript_client.submit(file_path, language)

        if media.transcription is None:
            print("Processing  transcription.")
            transcription = self.transcript_client.get_transcription_with_wait(media, max_wait=20)
            transcription = process_special_characters(transcription, language)
            print(f"Transcription for video {file_name}:\n{transcription}")
            media.transcription = transcription
            self.media_archive.add_media(media)

        if media.speech_segments is None:
            print("Identifying speech pauses.")
            speech_segments, pause_segments = self.voice_detector(file_path, pause_margin=self.pause_margin)
            transcription = sync_transcription_to_pauses(
                transcription=media.transcription,
                speech_segments=speech_segments)
            media.transcription = transcription
            media.pause_segments = pause_segments
            media.speech_segments = speech_segments
            self.media_archive.add_media(media)

        paragraphs = merge_transcript_words(
            transcribed_words=media.transcription.words,
            speech_segments=media.speech_segments
        )
        text = "\n".join(paragraphs)

        if correct_grammar and media.corrected_transcription is None:
            print("Correcting transcription grammar.")
            corrected_transcription = correct_transcription(
                text_str=text,
                transcription=media.transcription,
                language=media.language
            )
            media.corrected_transcription = corrected_transcription

        transcription = media.corrected_transcription if media.corrected_transcription is not None else media.transcription

        if find_repetitions and media.repetition_segments is None:
            print("Identifying repetitions.")
            repetition_segments = find_repetitions_timestamps(
                text_str=text,
                transcription=transcription,
                language=media.language
            )
            media.repetition_segments = repetition_segments

        cuts = media.pause_segments if media.repetition_segments is None else \
            merge_overlapping_cuts(media.repetition_segments + media.pause_segments)

        result_video_path = process_video(
            file_path=file_path,
            cuts=cuts,
            transcription=transcription,
            output_dir_path=result_dir,
            generate_subtitles=generate_subtitles,
            save_cuts=save_cuts
        )

        return result_video_path


if __name__ == '__main__':
    video_processor = VideoProcessor()
    video_processor.process_video(
        file_name='what-is-intelligence.mp3',
        language=Language.english,
        correct_grammar=False,
        generate_subtitles=False,
        find_repetitions=False,
        save_cuts=True
    )
    # video_processor.process_video('demo-en.mp4', language=Language.english)
