import numpy as np
import imageio
from PIL import Image, ImageFont, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip

# Prepare ASCII characters and font settings
chars = np.array(list("@%#*+=-:. "))
font = "./fonts/arial.ttf"  # Adjust this path to your actual font file location
fontsize = 20
boldness = 2
background = 255
reverse = False

# Load font and prepare bitmaps
font_ttf = ImageFont.truetype(font, size=fontsize)
bitmaps = {}
min_width = min_height = float('inf')
for char in chars:
    w, h = font_ttf.getsize(char)
    min_width, min_height = min(min_width, w), min(min_height, h)
    image = Image.new('RGB', (w, h), (background,) * 3)
    draw = ImageDraw.Draw(image)
    draw.text((0, -(fontsize // 6)), char, fill=(255 - background,) * 3, font=font_ttf, stroke_width=boldness)
    bitmap = np.array(image)
    if background == 255:
        np.subtract(255, bitmap, out=bitmap)
    bitmaps[char] = bitmap.astype(np.uint8)
font_bitmaps = np.array([bitmaps[char][: int(min_height), : int(min_width)] for char in chars])

# Define the ASCII effect function
def apply_ascii_effect(frame):
    # Apply ASCII processing to a frame
    h, w = frame.shape[:2]
    fh, fw = font_bitmaps[0].shape[:2]
    ascii_frame = frame[::fh, ::fw]
    return ascii_frame  # This should be replaced with complete ASCII processing logic

# Video processing functions
def process_video(input_path, output_path, target_width, target_height, shrink_factor):
    # Load the video
    clip = VideoFileClip(input_path)

    # Apply ASCII effect and create the background clip
    ascii_clip = clip.fl_image(apply_ascii_effect).resize(width=target_width, height=target_height)

    # Resize the original video
    small_clip = clip.resize(1.0 / shrink_factor)

    # Composite the videos
    final_clip = CompositeVideoClip([ascii_clip, small_clip.set_position(("center", "center"))])
    final_clip.write_videofile(output_path, codec="libx264")

# Example usage
input_video="data/processed/nature-of-intelligence-RO.mp4/segments/12-25-nature-of-intelligence-RO.mp4"
output_video="data/processed/nature-of-intelligence-RO.mp4/effect.mp4"
process_video(input_video, output_video, 1920, 1080, 2)
