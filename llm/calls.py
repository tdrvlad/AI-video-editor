from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from typing import List, Tuple, Union, Dict
from objects.transcription import TranscribedWord, Transcription
from objects.media_segment import MediaSegment
from llm.prompts import CORRECT_TRANSCRIPTION, CORRECT_GRAMMAR_WITH_SCRIPT, IS_REPETITION, FIND_REPETITIONS, GET_REPETITIONS_INDEXES, GET_SECTION_FROM_SCRIPT


def parse_output_as_code(output_str: str, language: str = 'json') -> str:
    startswith = f'```{language}'
    endswith = '```'
    if output_str.startswith(startswith) and output_str.endswith(endswith):
        output_str = output_str[len(startswith):][:-len(endswith)]
    return output_str


def call_llm(model_id: str, prompt: str, call_params_dict: dict) -> str:
    """
    Call a LLM.
    :param model_id: Id of the model to use (gpt-3.5-turbo / gpt-4)
    :param prompt: Prompt to use for the LLM
    :param call_params_dict: values for the parameters of the prompt
    :return: Return string of the model
    """
    model = ChatOpenAI(model=model_id, temperature=0)
    prompt_template = ChatPromptTemplate.from_messages(
        [("user", prompt)]
    )
    response = model.invoke(
        prompt_template.format_prompt(**call_params_dict)
    )
    return response.content


def correct_grammar_with_script(transcription: Transcription, text: str, script: str, language: str) -> Tuple[str, Transcription]:
    relevant_transcript = call_llm(
        model_id='gpt-3.5-turbo',
        prompt=GET_SECTION_FROM_SCRIPT,
        call_params_dict={
            "text": text,
            "script": script,
            "language": language
        }
    )
    corrected_text = call_llm(
        model_id='gpt-4',
        prompt=CORRECT_GRAMMAR_WITH_SCRIPT,
        call_params_dict={
            "text": text,
            "script": relevant_transcript,
            "language": language
        }
    )
    corrected_text = corrected_text.upper()
    content = call_llm(
        model_id='gpt-4',
        prompt=CORRECT_TRANSCRIPTION,
        call_params_dict={
            "corrected_text": corrected_text,
            "transcription": transcription,
            "language": language
        }

    )
    content = parse_output_as_code(content, 'json')
    try:
        corrected_transcript = eval(content)
        assert isinstance(corrected_transcript, List)
        corrected_transcript_words = []
        for word_dict in corrected_transcript:
            corrected_transcript_words.append(
                TranscribedWord(
                    word=word_dict.get("word").upper(),
                    start=word_dict.get("start"),
                    end=word_dict.get("end")
                )
            )
        return corrected_text, Transcription(words=corrected_transcript_words)
    except Exception as e:
        print(f'Unable to parse LLM response {content}: {e}')
        return corrected_text, Transcription(words=[])


class Repetition(BaseModel):
    failed_attempts: List[int]
    correct_attempt: int


def get_repetitions(segments_dict: Dict[int, MediaSegment]) -> List[Repetition]:

    language = list(segments_dict.values())[0].language
    sentences = [f"Sentence {ind}: {segment.corrected_text}" for ind, segment in segments_dict.items()]
    sentences_string = "\n".join(sentences)

    repetitions_info = call_llm(
        model_id='gpt-4',
        prompt=FIND_REPETITIONS,
        call_params_dict={
            "indexed_text": sentences_string,
            "language": language
        }
    )

    content = call_llm(
        model_id='gpt-4',
        prompt=GET_REPETITIONS_INDEXES,
        call_params_dict={
            "indexed_text": sentences_string,
            "language": language,
            "repetitions": repetitions_info
        }
    )

    content = parse_output_as_code(content, 'json')
    try:
        repetitions_dicts = eval(content)
        assert isinstance(repetitions_dicts, List)
        repetitions = []
        for repetition_dict in repetitions_dicts:
            repetitions.append(
                Repetition(
                    failed_attempts=repetition_dict.get("failed_sentences"),
                    correct_attempt=repetition_dict.get("correct_sentence")
                )
            )
        return repetitions
    except Exception as e:
        print(f'Unable to parse LLM response {content}: {e}')

    # repetitions = []
    # indexes_to_check = list(segments_dict.keys())
    # checked = False
    #
    # while checked is False:
    #     checked = True
    #     eliminated_index = None
    #     kept_index = None
    #     for i_1, i_2 in zip(indexes_to_check[:-1], indexes_to_check[1:]):
    #         sentence_1 = segments_dict.get(i_1).corrected_text
    #         sentence_2 = segments_dict.get(i_2).corrected_text
    #         language = segments_dict.get(i_1).language
    #         content = call_llm(
    #             model_id='gpt-4',
    #             prompt=IS_REPETITION,
    #             call_params_dict={
    #                 "sentence_1": sentence_1,
    #                 "sentence_2": sentence_2,
    #                 "language": language
    #             }
    #         )
    #         if "sentence_1" in content:
    #             eliminated_index = i_1
    #             kept_index = i_2
    #             break
    #
    #         if "sentence_2" in content:
    #             eliminated_index = i_2
    #             kept_index = i_1
    #             break
    #
    #         if 'none' in content:
    #             pass
    #
    #     if eliminated_index is not None:
    #         repetitions.append(
    #             Repetition(
    #                 failed_attempts=[eliminated_index],
    #                 correct_attempt=kept_index
    #             )
    #         )
    #     indexes_to_check.pop(eliminated_index)

    return repetitions


#
# def find_parts(text_str, transcription: Transcription, language, openai_model_id='gpt-4') -> Transcription:
#     print("\nSearching for parts in the speech.")
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", IDEAS_SUMMARY)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "language": language,
#             }
#         )
#     )
#     ideas_summary = response.content
#     print(f"Ideas in the text:\n{ideas_summary}\n")
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", SPLIT_TRANSCRIPT)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "ideas": ideas_summary,
#                 "language": language,
#                 "timestamps": transcription
#             }
#         )
#     )
#     content = response.content
#     print(content)
#     content = parse_output_as_code(content, 'json')
#
#     try:
#         parts = eval(content)
#         assert isinstance(parts, List)
#         parts_list = []
#         for part_dict in parts:
#             parts_list .append(
#                 TranscribedWord(
#                     word=part_dict["idea"],
#                     start=part_dict["start"],
#                     end=part_dict["end"]
#                 )
#             )
#         print(parts_list)
#         return parts_list
#     except Exception as e:
#         print(f'Unable to parse LLM response {content}: {e}')
#         return []
#
#
# def find_repetitions_timestamps(text_str, transcription: Transcription, language, openai_model_id='gpt-4') -> List[Tuple[float, float]]:
#     print("\nSearching for repetitions in speech. ")
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", HIGHLIGHT_REPETITIONS)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "language": language,
#             }
#         )
#     )
#     repetitions = response.content
#
#     print(repetitions)
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", EXTRACT_TIMESTAMPS)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "repetitions": repetitions,
#                 "language": language,
#                 "timestamps": transcription
#             }
#         )
#     )
#     content = response.content
#     content = parse_output_as_code(content, 'json')
#
#     try:
#         cuts = eval(content)
#         assert isinstance(cuts, List)
#         cuts = [(cut["cut_start"], cut["cut_end"]) for cut in cuts]
#         return cuts
#     except Exception as e:
#         print(f'Unable to parse LLM response {content}: {e}')
#         return []
#
#
# def correct_transcription(text_str, transcription: Transcription, language, openai_model_id='gpt-4') -> Transcription:
#     print("\nCorrecting transcription")
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", HIGHLIGHT_MISTAKES)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "language": language,
#             }
#         )
#     )
#     mistakes = response.content
#
#     print(mistakes)
#
#     model = ChatOpenAI(model=openai_model_id, temperature=0)
#     prompt_template = ChatPromptTemplate.from_messages(
#         [("user", CORRECT_TRANSCRIPTION)]
#     )
#     response = model.invoke(
#         prompt_template.format_prompt(
#             **{
#                 "text": text_str,
#                 "mistakes": mistakes,
#                 "language": language,
#                 "timestamps": transcription
#             }
#         )
#     )
#     content = response.content
#     content = parse_output_as_code(content, 'json')
#
#     try:
#         corrected_transcript = eval(content)
#         assert isinstance(corrected_transcript, List)
#         corrected_transcript_words = []
#         for word_dict in corrected_transcript:
#             corrected_transcript_words.append(
#                 TranscribedWord(
#                     word=word_dict["word"],
#                     start=word_dict["start"],
#                     end=word_dict["end"]
#                 )
#             )
#         return Transcription(words=corrected_transcript_words)
#     except Exception as e:
#         print(f'Unable to parse LLM response {content}: {e}')
#         return []
#
#
#
