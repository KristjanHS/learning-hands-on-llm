"""Notebook helpers for chat prompts plus file listing and download links.

The OpenAI-compatible client uses a placeholder key, so point it at a local server
(e.g. via ``OPENAI_BASE_URL`` in ``.env``) rather than a cloud account.
"""

import base64
import csv
import os

import ipywidgets as widgets
from dotenv import load_dotenv
from IPython.display import HTML, display
from openai import OpenAI

SYSTEM_PROMPT = "Answer briefly and directly."

load_dotenv(".env", override=True)
client = OpenAI(api_key="aaa")


def _chat(prompt: str) -> str | None:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    return completion.choices[0].message.content


def _is_visible(name: str) -> bool:
    return not name.startswith((".", "_"))


def read_csv_dict(csv_file_path):
    """Load a CSV file into ``{row_index: row_dict}``."""
    with open(csv_file_path, mode="r") as handle:
        return dict(enumerate(csv.DictReader(handle)))


def print_llm_response(prompt):
    """Print the model's answer to ``prompt``; non-string prompts raise ``ValueError``."""
    if not isinstance(prompt, str):
        raise ValueError("prompt must be a str")
    try:
        print(_chat(prompt))
    except TypeError as exc:
        print("Error:", exc)


def get_llm_response(prompt):
    """Return the model's answer to ``prompt`` as a string."""
    return _chat(prompt)


def read_journal(journal_file):
    """Return the full text of ``journal_file``."""
    with open(journal_file, "r") as handle:
        return handle.read()


def create_download_link(file_path, description):
    """Return an HTML anchor that downloads ``file_path`` from an inline base64 payload."""
    with open(file_path, "rb") as handle:
        payload = base64.b64encode(handle.read()).decode()
    return HTML(f'<a href="data:text/html;base64,{payload}" download="{file_path}">{description}</a>')


def download_file():
    """Show a filename box plus button that renders a download link for that file."""
    name_box = widgets.Text(value="", placeholder="file name", description="Name:", disabled=False)
    button = widgets.Button(
        description="Get link",
        disabled=False,
        button_style="",
        tooltip="Build a download link for the named file",
        icon="download",
    )
    output = widgets.Output()

    def on_click(_button):
        with output:
            output.clear_output()
            name = name_box.value
            if not _is_visible(name):
                print("Hidden or private files cannot be downloaded.")
                return
            try:
                display(create_download_link(name, "Download"))
            except Exception as exc:
                print(f"Error: {exc}")

    button.on_click(on_click)
    display(widgets.HBox([name_box, button]), output)


def list_files_in_directory(directory="."):
    """Print every entry in ``directory`` whose name does not start with ``.`` or ``_``."""
    try:
        for name in os.listdir(directory):
            if _is_visible(name):
                print(name)
    except Exception as exc:
        print(f"An error occurred: {exc}")
