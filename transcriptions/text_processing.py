import re
from typing import List

from transcriptions.objects import TranscribedWord, Language, Transcription


def normalize_text(text: str) -> List[str]:
    """ Normalize text by removing punctuation, converting to lower case, and splitting into words. """
    # Remove punctuation and convert to lower case
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text.split()


def process_special_characters(transcription: Transcription, language: str) -> Transcription:
    if language == Language.romanian:
        corrected_words = []
        for transcribed_word in transcription.words:
            transcribed_word.word = normalize_romanian_characters(transcribed_word.word)
            corrected_words.append(transcribed_word)
        return Transcription(words=corrected_words)
    return transcription


def normalize_romanian_characters(text: str) -> str:
    """
    Normalize Romanian characters to use the correct diacritical marks.
    Converts cedilla to comma variants for 's' and 't'.
    """
    replacements = {
        'ș': 'ş',  # Replace s with cedilla to s with comma
        'Ș': 'Ş',  # Replace capital S with cedilla to capital S with comma
        'ț': 'ţ',  # Replace t with cedilla to t with comma
        'Ț': 'Ţ'  # Replace capital T with cedilla to capital T with comma
    }
    # Replace each character in the text
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text