from pyannote.audio.pipelines import VoiceActivityDetection
from pyannote.audio import Model
import os
import dotenv
from typing import Tuple, List
dotenv.load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
VOICE_DETECTION_MODEL_ID = "pyannote/segmentation-3.0"


def parse_segments(segments_list) -> List[Tuple[float, float]]:
    parsed_segments = []
    for segment in segments_list:
        start, end = segment.start, segment.end
        parsed_segments.append((start, end))
    return parsed_segments


def merge_intervals(intervals, k):
    intervals.sort(key=lambda x: x[0])
    merged_intervals = []
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        # If the current end is close enough to the next start, merge them
        if current_end + k >= start:
            # Extend the current interval
            current_end = max(current_end, end)
        else:
            # Append the current interval and move to the next
            merged_intervals.append((current_start, current_end))
            current_start, current_end = start, end

    merged_intervals.append((current_start, current_end))
    return merged_intervals


class VoiceDetector:
    # onset: float = 0.5
    # offset: float = 0.5
    """
    onset: mark region as active when probability goes above value
    offset: switch back to inactive when probability goes below value
    min_duration_on: remove active regions shorter than that many seconds
    min_duration_off: fill inactive regions shorter than that many seconds
  
    More details about those hyper-parameters are provided in the paper: https://arxiv.org/abs/2104.04045 
    """

    def __init__(self, model_id: str = VOICE_DETECTION_MODEL_ID, min_duration_on: float = 0.0, min_duration_off: float = 0.0):
        self.model = Model.from_pretrained(
            model_id,
            use_auth_token=HF_TOKEN
        )
        self.min_duration_on = min_duration_on
        self.min_duration_off = min_duration_off
        self.pipeline = VoiceActivityDetection(segmentation=self.model)
        params = {
            # "onset": self.onset,
            # "offset": self.offset,
            "min_duration_on": min_duration_on,
            "min_duration_off": min_duration_off
        }
        self.pipeline.instantiate(params)

    def get_speech_segments(self, file_path: str, margin_start: float = 0.0, margin_end: float = 0.0) -> List[Tuple[float, float]]:
        """
        Returns the start and end timestamps for all the detected speech segments in the file.
        A segment is given as (start, end) timestamps in seconds
        :param file_path: Path to the file, accepts videos too.
        :param margin_start: Margin to be added to the beginning of the speech segment
        :param margin_end: Margin to be added at the end of the speech segment
        :return: The speech segments
        """
        voice_activity = self.pipeline(file_path)
        timeline = voice_activity.get_timeline()

        speech_segments = parse_segments(timeline.segments_list_)
        print(speech_segments)

        if margin_start > 0:
            print(f"Extending the speech segments with {margin_start} seconds from the start.")
        if margin_start < 0:
            print(f"Shortening the speech segments with {margin_start} seconds from the start.")
        if margin_end > 0:
            print(f"Extending the speech segments with {margin_end} seconds from the end.")
        if margin_end < 0:
            print(f"Shortening the speech segments with {margin_end} seconds from the end.")

        speech_segments = [(seg[0] - margin_start, seg[1] + margin_end) for seg in speech_segments]

        # Discard speech segments that are too short as a result of the margin adjustment
        speech_segments = [seg for seg in speech_segments if seg[1] - seg[0] > self.min_duration_on]

        # Merge the segments that have a too short pause between them
        speech_segments = merge_intervals(speech_segments, k=self.min_duration_off)

        return speech_segments


if __name__ == '__main__':
    voice_detector = VoiceDetector(min_duration_off=0.1)
    segments = voice_detector.get_speech_segments("./data/source/sample-3.mp4")
    print(segments)

    voice_detector = VoiceDetector(min_duration_off=1.0)
    segments = voice_detector.get_speech_segments("./data/source/sample-3.mp4", margin_start=0.2, margin_end=0.3)
    print(segments)
