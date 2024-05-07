from typing import List, Tuple
from utils import process_string
import numpy as np
from PIL import ImageFont, Image, ImageDraw
from moviepy.video.VideoClip import VideoClip
from moviepy.editor import VideoFileClip
import textwrap
from objects.transcription import TranscribedWord, Transcription

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


def add_text_outline(draw: ImageDraw.Draw, text_position: Tuple[int, int], text: str, font: ImageFont, outline_offset=10, shadow_color='black'):
    outline_coordinates = [
        (text_position[0] - outline_offset, text_position[1]),
        (text_position[0] + outline_offset, text_position[1]),
        (text_position[0], text_position[1] - outline_offset),
        (text_position[0], text_position[1] + outline_offset),
        (text_position[0] - outline_offset, text_position[1] - outline_offset),
        (text_position[0] + outline_offset, text_position[1] - outline_offset),
        (text_position[0] - outline_offset, text_position[1] + outline_offset),
        (text_position[0] + outline_offset, text_position[1] + outline_offset),
    ]
    for coord in outline_coordinates:
        draw.text(coord, text, font=font, fill=shadow_color)


def add_subtitles_to_frames(video: VideoFileClip, transcription: Transcription, font_path: str = FONT_PATH, font_size=100, h_pos=260, subtitles_window=0.9, normalize_text=True) -> VideoFileClip:
    print("Adding subtitles")
    transcription.words.sort(key=lambda x: x.start)
    font = ImageFont.truetype(font_path, size=font_size)

    subtitles = generate_transcription_subtitles(
        transcription=transcription,
        window=subtitles_window
    )

    def attach_subtitles(get_frame, t):
        frame = get_frame(t)
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)

        max_width = frame.shape[1]  # The maximum width for text

        text = ""
        for subtitle in subtitles:
            if subtitle.start <= t <= subtitle.end:
                text += subtitle.word
            if subtitle.start > t:
                break

        if normalize_text:
            text = process_string(text).upper()

        lines = textwrap.wrap(text, width=int(max_width / (font_size * 0.75)))
        y_text = frame.shape[0] - h_pos

        for line in lines:
            w, h = draw.textsize(line, font=font)
            position = ((max_width - w) // 2, y_text)

            add_text_outline(
                draw=draw,
                text_position=position,
                text=line,
                font=font,
                outline_offset=3,
                shadow_color='black'
            )

            # Draw the main white text
            draw.text(position, line, font=font, fill=(255, 255, 255))
            y_text += h  # Move text position for the next line

        return np.array(image)

    output_clip = video.fl(attach_subtitles)
    return output_clip


def process_video_with_subtitles(input_video_path, output_video_path, transcription, font_size=100, h_pos=260, subtitles_window=0.9, normalize_text=True):
    video = VideoFileClip(input_video_path)
    processed_video = add_subtitles_to_frames(
        video=video,
        transcription=transcription,
        font_size=font_size,
        h_pos=h_pos,
        subtitles_window=subtitles_window,
        normalize_text=normalize_text
    )
    processed_video.write_videofile(output_video_path, codec='libx264')
