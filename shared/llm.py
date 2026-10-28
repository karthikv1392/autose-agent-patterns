"""Shared LLM client — wraps Ollama (local inference).

Every pattern imports `generate` from here so the model configuration lives
in one place. Override the model with the AUTOSE_MODEL environment variable
or call `set_model()` (the Streamlit sidebar does this).
"""

import os

import ollama

MODEL = os.environ.get("AUTOSE_MODEL", "gemma4")

# Reasoning ("thinking") models spend many tokens on hidden chain-of-thought. These
# demos run dozens of calls, so thinking is OFF by default; set AUTOSE_THINK=1 to enable it.
THINK = os.environ.get("AUTOSE_THINK", "0") == "1"


def set_model(name: str) -> None:
    global MODEL
    MODEL = name


def generate(
    prompt: str,
    system: str | None = None,
    temperature: float | None = None,
    stop: list[str] | None = None,
) -> str:
    """Return the model's text response.

    temperature : lower = more deterministic. Pattern code sets this on purpose
                  (e.g. high for diverse voting candidates, low for fixing).
    stop        : strings that end generation early (used by the ReAct agent so
                  the model cannot hallucinate its own tool observations).
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if stop:
        options["stop"] = stop

    try:
        response = ollama.chat(model=MODEL, messages=messages, options=options or None, think=THINK)
    except ollama.ResponseError:
        # Model without thinking support: retry with the plain call.
        response = ollama.chat(model=MODEL, messages=messages, options=options or None)
    return response.message.content
