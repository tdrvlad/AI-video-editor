from typing import List

import numpy as np
from PIL import ImageFont, Image, ImageDraw
from moviepy.video.VideoClip import VideoClip

from transcriptions.objects import TranscribedWord, Transcription


FONT_PATH = "./fonts/arial.ttf"


def generate_transcription_subtitles(transcription: Transcription, window: float = 0.5) -> List[TranscribedWord]:
    subtitles = []
    if not transcription.words:
        return subtitles

    # Start with the first word
    current_start = transcription.words[0].start
    current_end = transcription.words[0].end
    current_sentence = transcription.words[0].word

    for word in transcription.words[1:]:
        # If the next word is within the time window, add it to the current group
        if word.start - current_start < window:
            current_sentence += ' ' + word.word
            current_end = max(current_end, word.end)
        else:
            # Otherwise, start a new group
            subtitle = TranscribedWord(
                word=current_sentence,
                start=current_start,
                end=current_end
            )
            subtitles.append(subtitle)
            current_start = word.start
            current_end = word.end
            current_sentence = word.word

    # Append the last group
    subtitle = TranscribedWord(
        word=current_sentence,
        start=current_start,
        end=current_end
    )
    subtitles.append(subtitle)
    return subtitles


def add_subtitles_to_frames(video: VideoClip, transcription: Transcription, font_path: str = FONT_PATH, font_size=100, h_pos=260) -> VideoClip:
    print("Adding subtitles")
    # Sort the transcription list by start time to ensure they are in the correct order
    transcription.words.sort(key=lambda x: x.start)
    font = ImageFont.truetype(font_path, size=font_size)  # Adjust size as needed

    subtitles = generate_transcription_subtitles(transcription)

    def attach_subtitles(get_frame, t):
        frame = get_frame(t)
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)

        # Find the appropriate subtitle for the current frame
        for subtitle in subtitles:
            if subtitle.start <= t <= subtitle.end:
                text = subtitle.word
                w, h = draw.textsize(text, font=font)
                position = ((frame.shape[1] - w) // 2, frame.shape[0] - h // 2 - h_pos)
                draw.text(position, text, font=font, fill=(255, 255, 255))
                break

        return np.array(image)

    output_clip = video.fl(attach_subtitles)
    return output_clip