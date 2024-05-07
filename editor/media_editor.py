from transcriptions.text_processing import process_special_characters
from objects.media_segment import MediaSegment, load_media_segments, save_media_segment
import os
from objects.media_clip import MediaClip
from utils import align_texts_indices
from voice_segmentation.voice_activity_detection import VoiceDetector
from editor.cut_media import cut_media, paste_media_segments
from objects.media_segment import SUBBED_SEGMENTS_DIR_NAME
from llm.calls import get_repetitions, correct_transcription_text
from utils import clear_and_create_dir
from subtitles import process_video_with_subtitles
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


def retrieve_segments_transcription(segments: List[MediaSegment], language: str, redo: bool = False) -> List[MediaSegment]:
    """
    Retrieve transcriptions for the segments.
    If the transcription does not exist, it is queried as a task in the TranscriptClient.
    :param segments: List of video segments
    :param language: Language for the transcription
    :param redo: If True, will regenerate Transcriptions from the client.
    :return: List of video segments with transcriptions.
    """
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


def clean_transcription(segments):
    for segment in segments:
        segment.transcription = process_special_characters(
            transcription=segment.transcription,
            language=segment.language
        )
        segment.corrected_transcription = process_special_characters(
            transcription=segment.corrected_transcription,
            language=segment.language
        )
        save_media_segment(segment)


def correct_video_transcription(file_name: str, segments: List[MediaSegment], redo: bool = False):
    if redo:
        for segment in segments:
            segment.grammar_is_checked = False
            segment.corrected_transcription = None
            segment.corrected_text = None
            segment.text = None
            save_media_segment(segment)
    
    script = get_script(file_name=file_name)
    for segment in segments:
        if segment.grammar_is_checked and segment.corrected_transcription is not None:
            continue

        print(f'\n\nCorrecting segment {int(segment.timestamp_start)} - {int(segment.timestamp_end)}:')
        original_words = [w.word for w in segment.transcription.words]
        corrected_transcript_text = correct_transcription_text(
            text=" ".join(original_words),
            script=script,
            language=segment.language,
            preview_fn=MediaClip(segment.media_file_path).preview_audio
        )

        corrected_words = corrected_transcript_text.split(' ')
        index_map = align_texts_indices(
            original_words=[w.word for w in segment.transcription.words],
            corrected_words=corrected_words
        )

        corrected_transcription_words = []
        for original_ind, transcription_word in enumerate(segment.transcription.words):
            if len(index_map[original_ind]):
                corresponding_corrected_words = [corrected_words[i] for i in index_map[original_ind]]
                transcription_word.word = " ".join(corresponding_corrected_words)
                corrected_transcription_words.append(transcription_word)

        corrected_text = " ".join([w.word for w in corrected_transcription_words])
        print(f"FINAL VERSION:\n'''\n{corrected_text}\n'''\n")

        segment.corrected_transcription = Transcription(words=corrected_transcription_words)
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
    segments = retrieve_segments_transcription(segments, language=language)

    # unfilter(segments)
    # filter_duplicates(segments)
    # manual_filter(segments)
    # manual_recover(segments)
    # filter_file_removed(segments)

    segments = [segment for segment in segments if not segment.removed]
    correct_video_transcription(file_name=file_name, segments=segments)
    clean_transcription(segments)

    # print("Adding subtitles.")
    # subbed_videos_dir = os.path.join(RESULT_VIDEOS_DIR, file_name, SUBBED_SEGMENTS_DIR_NAME)
    # clear_and_create_dir(subbed_videos_dir)
    # for segment in segments:
    #     file_path = segment.media_file_path
    #     result_file_path = os.path.join(subbed_videos_dir, os.path.basename(file_path))
    #     process_video_with_subtitles(
    #         input_video_path=file_path,
    #         output_video_path=result_file_path,
    #         transcription=segment.corrected_transcription,
    #         font_size=75,
    #         h_pos=450,
    #         subtitles_window=0.65
    #     )
    #     segment.subbed_media_file_path = result_file_path
    #     save_media_segment(segment)

    paste_media_segments(
        media_segments=segments,
        output_path=os.path.join(RESULT_VIDEOS_DIR, file_name, "result.mp4"),
        start_trim=0.0,
        end_trim=0.4,
        transition='None',
        transition_duration=0.1,
        use_subbed=True
    )


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


