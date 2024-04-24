HIGHLIGHT_MISTAKES = """
Here is a transcript of an audio file with a speech in {language}:
'''
{text}
'''
There are some mistakes from the speech-to-text engine that was used. 
Some words were mistakenly interpreted, probably because they sounded similar to other words. 
There might also be grammar or semantic problems. 

Identify all instances in the speech where there are such mistakes. 
Identify words that do not make sense and suggest a correction that should be mase.
Add punctuation where it is needed.
"""


CORRECT_TRANSCRIPTION = """
Here is a transcript of an audio file with a speech in {language}:
'''
{text}
'''
There are some mistakes from the speech-to-text engine that was used. 
Some words were mistakenly interpreted, probably because they sounded similar to other words. 
There might also be grammar or semantic problems. 

We have identified some parts where this happens:
{mistakes}

We now need to also apply these changes that correct the mistakes to the transcript that contains the timestamps for each word.
This is the original transcript with timestamps for each word:
{timestamps}

Now generate a similar transcript but with the corrected words. If punctuation was added, make it part of the word it follows.

Return a JSON list of dicts with the fields:
- start: timestamp in seconds
- end: timestamp in seconds
- word: corrected word

Return only the JSON dict without any additional text or explanation. If no highlights exist, return an empty list.
"""


HIGHLIGHT_REPETITIONS = """
Here is a transcript of an audio file with a speech in {language}:
'''
{text}
'''
The speaker sometimes starts a sentence, stops midway, and restarts it. 
This can happen multiple times for the same sentence as the speaker tries to find the correct formulation. 
The final successful attempt is where the sentence is fully completed without interruption.

Identify all instances in the speech where the speaker makes these repetitive errors. 
"""


EXTRACT_TIMESTAMPS = """
Here is a transcript of an audio file with a speech in {language}:
'''
{text}
'''
The speaker sometimes starts a sentence, stops midway, and restarts it. 
This can happen multiple times for the same sentence as the speaker tries to find the correct formulation. 
The final successful attempt is where the sentence is fully completed without interruption.

We have identified some parts where this happens:
{repetitions}

We now need to identify the exact timestamps of the cuts we need to make.
These are the timestamps of each word in the transcript:
{timestamps}

Return a JSON list of dicts with the fields:
- cut_start: timestamp in seconds
- cut_end`: timestamp in seconds

Return only the JSON dict without any additional text or explanation. If no highlights exist, return an empty list.
"""
