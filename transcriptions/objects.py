from typing import List

from pydantic import BaseModel


class Language:
    romanian: str = 'ro_RO'
    english: str = 'en_GB'


class TranscribedWord(BaseModel):
    word: str
    start: float
    end: float

    def __repr__(self):
        return f"{self.word} ({self.start}-{self.end})"

    def __str__(self):
        return self.__repr__()


class Transcription(BaseModel):
    words: List[TranscribedWord]

    def __repr__(self):
        return "\n".join([str(word) for word in self.words])

    def __str__(self):
        return self.__repr__()


def test():
    words = [
        TranscribedWord(word="This", start=0.1, end=0.3),
        TranscribedWord(word="is", start=0.4, end=0.6),
        TranscribedWord(word="me", start=0.7, end=0.9)
    ]
    transcription = Transcription(words=words)
    print(transcription)


if __name__ == '__main__':
    test()