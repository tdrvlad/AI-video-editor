# IS_DUPLICATE = """
# We are processing a transcript of a speech.
#
# The speaker sometimes starts a sentence, stops midway, and restarts it.
# This can happen multiple times for the same sentence as the speaker tries to find the correct formulation.
# The final successful attempt is where the sentence is fully completed without interruption.
#
# Does this happen for the CURRENT SENTENCE?
# {text}
#
# Respond only with the string 'YES' or 'NO'
# """


GET_SECTION_FROM_SCRIPT = """
Here is a section from a transcript of a speech in {language}:
'''
{text}
'''
This is the raw script that was used as a guidance for the speaker. 
'''
{script}
'''
The speaker might not have followed the script with 100% accuracy.

Find the section of the script that corresponds to the transcript section.
Select the section of the script and return it here:


"""
CORRECT_GRAMMAR_WITH_SCRIPT = """
Here is a section from a transcript of a speech in {language}:
'''
{text}
'''
There are some mistakes in the transcription, some words were confused with words that sound similar. 
There might also be grammar mistakes.

Correct the transcription.

As a guidance, here is the speaker's plan:
'''
{script}
'''
The speaker did not use the plan word by word but you can make out the overall idea in order to decide which is the correct word.

Return the corrected transcription in {language}.
"""


CORRECT_TRANSCRIPTION = """
Here is a transcript of a speech in {language}:
{transcription}

There are some mistakes in the transcription. This is the corrected text:
{corrected_text}

Generate the corresponding transcript with timestamps for each word in the corrected text, based on the initial transcript.

Return a JSON list of dicts with the fields:
- start: timestamp in seconds
- end: timestamp in seconds
- word: corrected word

Return only the JSON dict without any additional text or explanation
"""

EXTRACT_INDEXES = """
Here is the response of a LLM providing a list of indexes.

Extract and return the list of indexes as a python list of ints, without any additional text.
"""

FIND_REPETITIONS = """
Here is a transcript of of a speech, provided as individual sentences.
'''
{indexed_text}
'''
You have both the corrected version of the transcription and the raw text, that might contain mistakes, in brackets.

The speaker sometimes stutters - starts a sentence, stops midway, and restarts it.
This can happen multiple times for the same phrase as the speaker tries to find the correct formulation.
You can see this in consecutive sentences where very similar words are used.

Identify where these mistakes happen. 
"""

GET_REPETITIONS_INDEXES = """
Here is a transcript of of a speech, provided as individual sentences.
'''
{indexed_text}
'''
You have both the corrected version of the transcription and the raw text, that might contain mistakes, in brackets.

The speaker sometimes stutters - starts a sentence, stops midway, and restarts it.
This can happen multiple times for the same phrase as the speaker tries to find the correct formulation.

This is where such mistakes occur:
{repetitions}

For each mistake, we need to select the correct sentence and eliminate the failed attempts. 
Decide based on the highlighted sentences, which sentences to keep and which to discard.

There can be multiple failed in a row. 
Usually, the correct sentence is the last one.

Return a list of JSON dictionaries for each corrected repetition like this:
- failed_attempts_indexes: list of int indexes of sentences that represent failed attempts.
- correct_attempt_index: int index representing the correct version of the failed attempts. 

Each failed attempt must have one corresponding correct attempt.
Each correct attempt can have one or more corresponding failed attempts.

Return the JSON list of dictionaries without any additional text - only the list of ints
"""


#
#
# IDEAS_SUMMARY = """
# Here is a transcript of an audio in {language} representing a monologue / discussion on a specific topic.
# '''
# {text}
# '''
# Identify the main ideas / arguments being made. Highlight what is relevant.
# Describe where each of these ideas start and end in the span of the text
# """
#
#
# SPLIT_TRANSCRIPT = """
# Here is a transcript of an audio in {language} representing a monologue / discussion on a specific topic.
# '''
# {text}
# '''
# Here are the main ideas i the text:
# '''
# {ideas}
# '''
#
# We now need to split the transcript into the parts corresponding to each idea.
# We have the transcript with timestamps for each word.
# Your task is to identify based on the transcript and the summary of the ideas when each part starts and ends.
#
# This is the complete transcript:
# '''
# {timestamps}
# '''
#
# List the start and end timestamps corresponding to each idea.
# Return a JSON list of dicts with the fields:
# - start: timestamp in seconds
# - end: timestamp in seconds
# - idea: idea summary
#
# Return only the JSON object without any additional text or explanation
# """
#
#
#
#
#
# HIGHLIGHT_MISTAKES = """
# Here is a transcript of an audio file with a speech in {language}:
# '''
# {text}
# '''
# There are some mistakes from the speech-to-text engine that was used.
# Some words were mistakenly interpreted, probably because they sounded similar to other words.
# There might also be grammar or semantic problems.
#
# Identify all instances in the speech where there are such mistakes.
# Identify words that do not make sense and suggest a correction that should be mase.
# Add punctuation where it is needed.
# """
#
#
# CORRECT_TRANSCRIPTION = """
# Here is a transcript of an audio file with a speech in {language}:
# '''
# {text}
# '''
# There are some mistakes from the speech-to-text engine that was used.
# Some words were mistakenly interpreted, probably because they sounded similar to other words.
# There might also be grammar or semantic problems.
#
# We have identified some parts where this happens:
# {mistakes}
#
# We now need to also apply these changes that correct the mistakes to the transcript that contains the timestamps for each word.
# This is the original transcript with timestamps for each word:
# {timestamps}
#
# Now generate a similar transcript but with the corrected words. If punctuation was added, make it part of the word it follows.
#
# Return a JSON list of dicts with the fields:
# - start: timestamp in seconds
# - end: timestamp in seconds
# - word: corrected word
#
# Return only the JSON dict without any additional text or explanation. If no highlights exist, return an empty list.
# """
#
#


# EXTRACT_TIMESTAMPS = """
# Here is a transcript of an audio file with a speech in {language}:
# '''
# {text}
# '''
# The speaker sometimes starts a sentence, stops midway, and restarts it.
# This can happen multiple times for the same sentence as the speaker tries to find the correct formulation.
# The final successful attempt is where the sentence is fully completed without interruption.
#
# We have identified some parts where this happens:
# {repetitions}
#
# We now need to identify the exact timestamps of the cuts we need to make.
# These are the timestamps of each word in the transcript:
# {timestamps}
#
# Return a JSON list of dicts with the fields:
# - cut_start: timestamp in seconds
# - cut_end`: timestamp in seconds
#
# Return only the JSON dict without any additional text or explanation. If no highlights exist, return an empty list.
# """
