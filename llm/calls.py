from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from typing import List, Tuple
from transcriptions.objects import Transcription, TranscribedWord
from llm.prompts import HIGHLIGHT_MISTAKES, CORRECT_TRANSCRIPTION, HIGHLIGHT_REPETITIONS, EXTRACT_TIMESTAMPS


def parse_output_as_code(output_str: str, language: str = 'json') -> str:
    startswith = f'```{language}'
    endswith = '```'
    if output_str.startswith(startswith) and output_str.endswith(endswith):
        output_str = output_str[len(startswith):][:-len(endswith)]
    return output_str


def find_repetitions_timestamps(text_str, transcription: Transcription, language, openai_model_id='gpt-4') -> List[Tuple[float, float]]:
    print("\nSearching for repetitions in speech. ")

    model = ChatOpenAI(model=openai_model_id, temperature=0)
    prompt_template = ChatPromptTemplate.from_messages(
        [("user", HIGHLIGHT_REPETITIONS)]
    )
    response = model.invoke(
        prompt_template.format_prompt(
            **{
                "text": text_str,
                "language": language,
            }
        )
    )
    repetitions = response.content

    print(repetitions)

    model = ChatOpenAI(model=openai_model_id, temperature=0)
    prompt_template = ChatPromptTemplate.from_messages(
        [("user", EXTRACT_TIMESTAMPS)]
    )
    response = model.invoke(
        prompt_template.format_prompt(
            **{
                "text": text_str,
                "repetitions": repetitions,
                "language": language,
                "timestamps": transcription
            }
        )
    )
    content = response.content
    content = parse_output_as_code(content, 'json')

    try:
        cuts = eval(content)
        assert isinstance(cuts, List)
        cuts = [(cut["cut_start"], cut["cut_end"]) for cut in cuts]
        return cuts
    except Exception as e:
        print(f'Unable to parse LLM response {content}: {e}')
        return []


def correct_transcription(text_str, transcription: Transcription, language, openai_model_id='gpt-4') -> Transcription:
    print("\nCorrecting transcription")

    model = ChatOpenAI(model=openai_model_id, temperature=0)
    prompt_template = ChatPromptTemplate.from_messages(
        [("user", HIGHLIGHT_MISTAKES)]
    )
    response = model.invoke(
        prompt_template.format_prompt(
            **{
                "text": text_str,
                "language": language,
            }
        )
    )
    mistakes = response.content

    print(mistakes)

    model = ChatOpenAI(model=openai_model_id, temperature=0)
    prompt_template = ChatPromptTemplate.from_messages(
        [("user", CORRECT_TRANSCRIPTION)]
    )
    response = model.invoke(
        prompt_template.format_prompt(
            **{
                "text": text_str,
                "mistakes": mistakes,
                "language": language,
                "timestamps": transcription
            }
        )
    )
    content = response.content
    content = parse_output_as_code(content, 'json')

    try:
        corrected_transcript = eval(content)
        assert isinstance(corrected_transcript, List)
        corrected_transcript_words = []
        for word_dict in corrected_transcript:
            corrected_transcript_words.append(
                TranscribedWord(
                    word=word_dict["word"],
                    start=word_dict["start"],
                    end=word_dict["end"]
                )
            )
        return Transcription(words=corrected_transcript_words)
    except Exception as e:
        print(f'Unable to parse LLM response {content}: {e}')
        return []



