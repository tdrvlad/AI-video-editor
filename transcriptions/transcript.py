from typing import List, Tuple

from objects.transcription import TranscribedWord


def merge_transcript_words(transcribed_words: List[TranscribedWord], speech_segments: List[Tuple[float, float]]):
    """
        Merge words into paragraphs, separating them based on specified pauses.

        Args:
        transcribed_words (list of TranscribedWord): The transcribed words.
        pauses (list of tuples): Each tuple contains the start and end of a pause.

        Returns:
        list of str: Each string is a paragraph formed from words between pauses.
        """
    paragraphs = []
    timestamped_paragraphs = []
    current_paragraph_words = []
    pause_index = 0

    paragraph_start, paragraph_end = speech_segments[pause_index]

    for word in transcribed_words:
        if word.end <= paragraph_end:
            current_paragraph_words.append(word)
        else:
            paragraph_string = " ".join([w.word for w in current_paragraph_words])
            paragraphs.append(paragraph_string)
            current_paragraph_words = [word]
            pause_index += 1
            paragraph_start, paragraph_end = speech_segments[pause_index]

    if len(current_paragraph_words):
        paragraphs.append(" ".join([w.word for w in current_paragraph_words]))

    return paragraphs


