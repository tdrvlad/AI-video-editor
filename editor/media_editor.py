import glob
from objects.media_archive import MediaArchive, Media
from objects.media_segment import MediaSegment, load_media_segments, save_media_segment
from typing import List, Optional
import os
from voice_segmentation.voice_activity_detection import VoiceDetector
from editor.cut_media import cut_media
from llm.calls import correct_grammar_with_script, get_repetitions
from transcriptions.api_client import TranscriptClient
from objects.transcription import Transcription
from objects.language import Language
from typing import List

SOURCE_VIDEOS_DIR = os.getenv("SOURCE_VIDEOS_DIR")
RESULT_VIDEOS_DIR = os.getenv("RESULT_VIDEOS_DIR")
SCRIPTS_DIR = os.getenv("SCRIPTS_DIR")


def cut_video_pauses(
    file_name: str,
    min_duration_on: float = 0.0,
    min_duration_off: float = 0.0,
    margin_start: float = 0.0,
    margin_end: float = 0.0
):
    """
    Remove pauses from an audio / video file based on detected speech.
    :param file_path: Path to the file
    :param min_duration_on: Speech segments shorter than this will be ignored (considered pauses)
    :param min_duration_off: Pause segments shorter than this will be ignored (considered speech)
    :param margin_start: Extend the speech segments start (if negative, will shorten the speech segment)
    :param margin_end: Extend the speech segments end (if negative, will shorten the speech segment)
    :return:
    """
    file_path = os.path.join(SOURCE_VIDEOS_DIR, file_name)

    voice_detector = VoiceDetector(
        min_duration_on=min_duration_on,
        min_duration_off=min_duration_off
    )
    speech_segments = voice_detector.get_speech_segments(
        file_path=file_path,
        margin_start=margin_start,
        margin_end=margin_end
    )

    cut_media(
        file_path=file_path,
        output_dir_path=os.path.join(RESULT_VIDEOS_DIR, file_name),
        segments_to_keep=speech_segments
    )


def process_transcription(segments: List[MediaSegment], language: str, redo: bool = False) -> List[MediaSegment]:
    transcript_client = TranscriptClient()

    for segment in segments:
        if segment.transcription_uuid is None:
            segment.transcription_uuid = transcript_client.submit(
                file_path=segment.media_file_path,
                language=language
            )
            save_media_segment(segment)

    for segment in segments:
        if segment.transcription is None or redo:
            segment.transcription = transcript_client.get_transcription_with_wait(
                    max_wait=30,
                    transcription_uuid=segment.transcription_uuid
            )
            segment.text = " ".join([w.word for w in segment.transcription.words])
            segment.language = language
            save_media_segment(segment)
        if segment.text is None:
            segment.text = " ".join([w.word for w in segment.transcription.words])
            save_media_segment(segment)
    return segments


def get_script(file_name: str):
    script_path = os.path.join(SCRIPTS_DIR, file_name + '.txt')
    if os.path.exists(script_path):
        with open(script_path, 'r', encoding='utf-8') as file:
            file_contents = file.read()
    else:
        # File does not exist, create a blank file
        with open(script_path, 'w', encoding='utf-8') as file:
            file_contents = ""  # This initializes an empty string for file contents
    if len(file_contents):
        return file_contents
    return None


def correct_transcription(file_name: str, segments: List[MediaSegment], redo: bool = False):
    script = get_script(file_name=file_name)
    for segment in segments:
        if segment.grammar_is_checked and not redo:
            continue

        _, corrected_transcription = correct_grammar_with_script(
            transcription=segment.transcription,
            text=segment.text,
            script=script,
            language=segment.language
        )
        corrected_text = " ".join([w.word for w in corrected_transcription.words])
        print(f"\nCorrection:\nIN: {segment.text}\nOUT: {corrected_text}")

        segment.corrected_transcription = corrected_transcription
        segment.corrected_text = corrected_text
        segment.grammar_is_checked = True
        save_media_segment(segment)

    print("Finished correcting the transcript.")


def unfilter(segments: List[MediaSegment]):
    for segment in segments:
        segment.removed = False
        save_media_segment(segment)


def manual_filter(segments: List[MediaSegment], ignore_already_filtered: bool = True):
    print("\nManually filtering transcripts.")
    if ignore_already_filtered:
        segments = [segment for segment in segments if not segment.removed]

    segments_dict = {i: segment for i, segment in enumerate(segments)}
    segments_texts_dict = {i: f"{segment.corrected_text} ({segment.text})" for i, segment in segments_dict.items()}

    indexed_text = "\n\n".join([f"{idx}: '{text}'" for idx, text in segments_texts_dict.items()])
    print(f"Transcription segments:\n{indexed_text}")

    input_string = input("Enter a list of indexes to remove (separated by spaces):")

    if not len(input_string):
        return

    try:
        indexes = [int(num) for num in input_string.split()]
        print("Removing:", indexes)

        for index in indexes:
            segment = segments_dict.get(index)
            if segment is None:
                print(f"No segment for index {index}.")
            segment.removed = True
            save_media_segment(segment)
    # 6 7 14 15 16 19 22 23 24 28 30 31 32 34 35 36 38 40 43 45
    except ValueError:
        print("Error: Please make sure to enter only integers.")


def manual_recover(segments: List[MediaSegment]):
    print("\nRecovering transcripts.")
    segments = [segment for segment in segments if segment.removed]

    segments_dict = {i: segment for i, segment in enumerate(segments)}
    segments_texts_dict = {i: f"{segment.corrected_text} ({segment.text})" for i, segment in segments_dict.items()}

    indexed_text = "\n\n".join([f"{idx}: '{text}'" for idx, text in segments_texts_dict.items()])
    print(f"Removed transcription segments:\n{indexed_text}")

    input_string = input("Enter a list of indexes to recover (separated by spaces):")

    if not len(input_string):
        return

    try:
        indexes = [int(num) for num in input_string.split()]
        print("Recovering:", indexes)

        for segment in [segments_dict.get(i) for i in indexes]:
            segment.removed = False
            save_media_segment(segment)

    except ValueError:
        print("Error: Please make sure to enter only integers.")


def filter_duplicates(segments: List[MediaSegment], ignore_already_filtered: bool = True):
    print("\n\nFiltering Duplicates")
    if ignore_already_filtered:
        segments = [segment for segment in segments if not segment.removed]

    segments_dict = {i: segment for i, segment in enumerate(segments)}
    # segments_texts_dict = {i: f"{segment.corrected_text} ({segment.text})" for i, segment in segments_dict.items()}

    repetitions = get_repetitions(
        segments_dict=segments_dict
    )

    for repetition in repetitions:

        correct_segment = segments_dict.get(repetition.correct_attempt)
        correct_text = correct_segment.corrected_text

        failed_segments = [segments_dict.get(i) for i in repetition.failed_attempts]
        failed_texts = [seg.corrected_text for seg in failed_segments]
        failed_texts_str = "\n".join(failed_texts)

        if repetition.correct_attempt in repetition.failed_attempts:
            print("\nRepetition correct attempt in failed attempts!")

        print(f"\nFound repetition:\nCORRECT:{correct_text}\n\nFAILS:{failed_texts_str}")
        user_input = input("Confirm removal of failed texts (Y/N):")

        if user_input.lower() == 'y':
            for segment in failed_segments:
                segment.removed = True
                save_media_segment(segment)
        else:
            print("Operation cancelled.")

    removed_segments = [segment for segment in segments if segment.removed]
    print(f"Removed {len(removed_segments)} segments due to repetitions.")


def filter_file_removed(segments: List[MediaSegment]):
    for segment in segments:
        if not os.path.exists(segment.media_file_path):
            print(f"Video for segment {segment.corrected_text} has been removed.")
            segment.removed = True
            save_media_segment(segment)


def main(file_name: str, language: str):
    segments = load_media_segments(file_name=file_name)
    segments = process_transcription(segments, language=language)

    for segment in segments:
        print(segment.corrected_text)
        # print(f"{segment.timestamp_start}-{segment.timestamp_end}:\n{segment.text}")

    correct_transcription(file_name=file_name, segments=segments)

    # unfilter(segments)
    # filter_duplicates(segments)
    # manual_filter(segments)
    # manual_recover(segments)
    filter_file_removed(segments)

    final_segments = [segment for segment in segments if not segment.removed]
    print("\n\nFinal Video Transcript:")
    for segment in final_segments:
        # print(f"{segment.timestamp_start}-{segment.timestamp_end}:\n{segment.corrected_text}")
        print(segment.corrected_text)



if __name__ == "__main__":
    file_name = 'nature-of-intelligence-RO.mp4'
    # cut_video_pauses(
    #     file_name=file_name,
    #     min_duration_on=1.0,
    #     min_duration_off=0.5,
    #     margin_start=0.3,
    #     margin_end=0.2
    # )
    main(
        file_name=file_name,
        language=Language.romanian
    )


