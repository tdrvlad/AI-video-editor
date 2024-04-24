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


class VoiceDetector:
    pause_margin: Tuple[float, float] = (0.0, 0.0)
    min_duration_on: float = 0.0
    min_duration_off: float = 0.0
    # onset: float = 0.5
    # offset: float = 0.5
    """
    onset: mark region as active when probability goes above value
    offset: switch back to inactive when probability goes below value
    min_duration_on: remove active regions shorter than that many seconds
    min_duration_off: fill inactive regions shorter than that many seconds
  
    More details about those hyper-parameters are provided in the paper: https://arxiv.org/abs/2104.04045 
    """

    def __init__(self, model_id: str = VOICE_DETECTION_MODEL_ID):
        self.model = Model.from_pretrained(
            model_id,
            use_auth_token=HF_TOKEN
        )
        self.pipeline = VoiceActivityDetection(segmentation=self.model)
        params = {
            # "onset": self.onset,
            # "offset": self.offset,
            "min_duration_on": self.min_duration_on,
            "min_duration_off": self.min_duration_off
        }
        self.pipeline.instantiate(params)

    def __call__(self, file_path: str, pause_margin: Tuple[float, float] = None) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """
        Returns the speech segments and the pause segments for the given file.
        A segment is given as (start, end) timestamps in seconds
        :param file_path: Path to the file, accepts videos too.
        :return: The speech and pause segments
        """

        voice_activity = self.pipeline(file_path)
        timeline = voice_activity.get_timeline()
        pause_timeline = timeline.gaps()

        speech_segments = parse_segments(timeline.segments_list_)
        pause_segments = parse_segments(pause_timeline.segments_list_)

        # Add pause margins
        if pause_margin is None:
            pause_margin = self.pause_margin
        print(f"Adding pause margin {pause_margin}")
        pause_segments = [(pause[0] + pause_margin[0], pause[1] - pause_margin[1]) for pause in pause_segments]

        # Add segments before first and after last utterance
        first_pause = (0.0, speech_segments[0][0] - pause_margin[1])
        last_pause = (speech_segments[-1][1] + pause_margin[0], 9999)

        pause_segments = [first_pause] + pause_segments + [last_pause]
        print(f"\nIdentified {len(pause_segments)} speech pauses.")
        return speech_segments, pause_segments

    def get_pauses(self, file_path: str, pause_margin: Tuple[float, float] = None) -> List[Tuple[float, float]]:
        _, pause_segments = self.__call__(file_path, pause_margin=pause_margin)
        return pause_segments

    def get_speech(self, file_path: str, pause_margin: Tuple[float, float] = None) -> List[Tuple[float, float]]:
        speech_segments, _ = self.__call__(file_path, pause_margin=pause_margin)
        return speech_segments


if __name__ == '__main__':
    voice_detector = VoiceDetector()
    speech_segments, _ = voice_detector("./data/source/sample-2.mp4")
    print(speech_segments)

