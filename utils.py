import os
import re
import shutil
from typing import List, Dict

import numpy as np


def clear_and_create_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)


def process_string(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ăâîșțşţ]', '', text)
    return text


def align_texts_indices(original_words: List[str], corrected_words: List[str]) -> Dict[int, List[int]]:
    """
    Infers the corresponding matches from the original words to the corrected words.
    Returns a dictionary where the keys are indexes of the original words and the values are lists of indexes of 
    the corresponding corrected words. If an original word is not matched by any corrected word, it has an empty list.
    :param original_words: List of strings with the original words
    :param corrected_words: List of strings with the corected words
    :return: A dictionary mapping
    """""

    original_words = [process_string(word) for word in original_words]
    corrected_words = [process_string(word) for word in corrected_words]

    # Create a 2D array to store the cost of alignments
    len_orig = len(original_words)
    len_corr = len(corrected_words)
    dp = np.zeros((len_orig + 1, len_corr + 1), dtype=int)

    # Initialize the array with maximum distances
    for i in range(len_orig + 1):
        dp[i][0] = i
    for j in range(len_corr + 1):
        dp[0][j] = j

    # Fill in the dp table
    for i in range(1, len_orig + 1):
        for j in range(1, len_corr + 1):
            sub_cost = 0 if original_words[i - 1][0] == corrected_words[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + sub_cost,  # substitution
                           dp[i - 1][j] + 1,  # deletion
                           dp[i][j - 1] + 1)  # insertion

    # Trace back to find the best alignment
    i, j = len_orig, len_corr
    index_map = {k: [] for k in range(len_orig)}  # Mapping of original indices to corrected indices

    while i > 0 and j > 0:
        if dp[i][j] == dp[i - 1][j - 1] + (0 if original_words[i - 1][0] == corrected_words[j - 1] else 1):
            index_map[i - 1].append(j - 1)
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + 1:
            # index_map[i-1] remains an empty list if no corrected word matches
            i -= 1
        else:
            if i < len_orig:  # Ensure we don't map out of range
                index_map[i].append(j - 1)
            j -= 1

    # Reverse the lists to maintain the order of the corrected indices
    for key in index_map:
        index_map[key].reverse()

    return index_map