"""Chat notebook helpers, wired to a local Ollama server.

``get_llm_response`` talks to Ollama through LangChain; the remaining helpers keep
using an OpenAI-compatible client configured from ``.env``.
"""

import csv
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from openai import OpenAI

SYSTEM_PROMPT = "Answer briefly and directly."

load_dotenv(".env", override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _chat(prompt: str, model: str) -> str | None:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    return completion.choices[0].message.content


def read_csv_dict(csv_file_path):
    """Load a CSV file into ``{row_index: row_dict}``."""
    with open(csv_file_path, mode="r") as handle:
        return dict(enumerate(csv.DictReader(handle)))


def print_llm_response(prompt):
    """Print the model's answer to ``prompt``; non-string prompts raise ``ValueError``."""
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a str")
    try:
        print(_chat(prompt, "gpt-4o-mini"))
    except TypeError as exc:
        print("Error:", exc)


def get_llm_response(
    prompt: str,
    *,
    model: str = "mistral",
    base_url: str = "http://localhost:11434",
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float = 0.0,
) -> str:
    """Ask a local Ollama model and return its whole (non-streamed) reply."""
    llm = ChatOllama(
        model=model,
        base_url=base_url,
        system=system_prompt,
        temperature=temperature,
        streaming=False,
    )
    message: AIMessage = llm.invoke(prompt)
    return message.content.strip() + "\n VER 3 WORKS!"


def get_chat_completion(prompt, history):
    """Answer ``prompt`` with the earlier turns in ``history`` prepended as plain text."""
    transcript = "\n\n".join("\n".join(turn) for turn in history)
    return _chat(f"{transcript}\n\n{prompt}", "gpt-3.5-turbo-0125")
