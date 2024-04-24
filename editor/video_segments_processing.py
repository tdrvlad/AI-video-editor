from typing import List, Tuple

from transcriptions.objects import TranscribedWord, Transcription


def merge_overlapping_cuts(cuts: List[Tuple[float, float]], min_duration: float = 0.3) -> List[Tuple[float, float]]:
    cuts = sorted(cuts, key=lambda x: x[0])

    overlaps = []
    current_overlap = []

    for i in range(len(cuts) - 1):
        if cuts[i][1] + min_duration > cuts[i + 1][0]:
            if not current_overlap:
                current_overlap = [i]
            current_overlap.append(i + 1)
        else:
            if current_overlap:
                overlaps.append(current_overlap)
                current_overlap = []

    # Add the last overlapping group if any
    if current_overlap:
        overlaps.append(current_overlap)

    print(f"Found {len(overlaps)} overlapping cuts {overlaps}")
    merged_cuts = []
    skip_indices = set()

    for idx, group in enumerate(overlaps):
        # Calculate the merged start and end for the current overlapping group
        start = cuts[group[0]][0]
        end = max(cuts[i][1] for i in group)
        merged_cuts.append((start, end))
        skip_indices.update(group)

    # Add non-overlapping cuts
    for i in range(len(cuts)):
        if i not in skip_indices:
            merged_cuts.append(cuts[i])

    # Return sorted merged cuts
    return sorted(merged_cuts, key=lambda x: x[0])


def sync_transcribed_word(word: TranscribedWord, speech_segments: List[Tuple[float, float]]) -> TranscribedWord:
    for segment_start, segment_end in speech_segments:
        if segment_start <= word.start <= segment_end:
            if segment_end < word.end:
                corrected_word = TranscribedWord(
                    word=word.word,
                    start=word.start,
                    end=segment_end
                )
                print(f"Synced {word.word} ({word.start}-{word.end}) to ({corrected_word.start}-{corrected_word.end})")
                return corrected_word
            return word
    return word


def sync_transcription_to_pauses(transcription: Transcription, speech_segments: List[Tuple[float, float]]):
    print("\nSyncing transcription to speech pauses.")
    corrected_words = [sync_transcribed_word(word, speech_segments) for word in transcription.words]
    return Transcription(words=corrected_words)
