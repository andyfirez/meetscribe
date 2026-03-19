"""Interview evaluation generation using local LLMs via Ollama.

Sends the call transcript to a local Ollama model and returns a structured
Markdown rubric: five criteria (1–5), explanations, total score, and
admission recommendation.

Requires Ollama running locally (http://localhost:11434).
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import requests

# ─── Constants ──────────────────────────────────────────────────────────────

DEFAULT_MODEL = "qwen3.5:9b"
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 600  # 10 minutes max

from meet.languages import LANG_NAMES as _LANGUAGE_NAMES  # noqa: E402

_PROMPT_CACHE: dict[str, str] = {}


def _load_prompt_file(name: str) -> str:
    """Load a UTF-8 prompt template from meet/prompts (cached)."""
    if name not in _PROMPT_CACHE:
        _PROMPT_CACHE[name] = files("meet.prompts").joinpath(name).read_text(encoding="utf-8")
    return _PROMPT_CACHE[name]


def _build_system_prompt(language: str | None = None) -> str:
    """Build the system prompt; optional block forces output language."""
    lang = language or "en"

    lang_instruction = ""
    if lang != "en" and lang in _LANGUAGE_NAMES:
        lang_name = _LANGUAGE_NAMES[lang]
        lang_instruction = (
            f"\n\n### ЯЗЫК ОТВЕТА\n"
            f"Оформи весь текст оценки (заголовки разделов, пояснения, "
            f"таблица, рекомендация) на {lang_name}."
        )

    tpl = _load_prompt_file("summary_system.txt")
    return tpl.format(lang_instruction=lang_instruction)


# ─── Data classes ───────────────────────────────────────────────────────────

@dataclass
class SummaryConfig:
    """Configuration for interview evaluation generation."""

    model: str = DEFAULT_MODEL
    ollama_url: str = OLLAMA_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    temperature: float = 0.2
    num_ctx: int = 32768


@dataclass
class MeetingSummary:
    """Result of interview evaluation generation (saved as .summary.md)."""

    markdown: str
    model: str
    elapsed_seconds: float

    def save(self, output_dir: str | Path, basename: str) -> Path:
        """Save the evaluation as a .summary.md file.

        Returns the path to the saved file.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{basename}.summary.md"
        path.write_text(self.markdown, encoding="utf-8")
        return path


# ─── Ollama availability check ─────────────────────────────────────────────

def is_ollama_available(url: str = OLLAMA_BASE_URL) -> bool:
    """Check if Ollama is running and reachable."""
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        return resp.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def list_models(url: str = OLLAMA_BASE_URL) -> list[str]:
    """List available Ollama models."""
    try:
        resp = requests.get(f"{url}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ─── Core summarization ────────────────────────────────────────────────────

def summarize(
    transcript_text: str,
    config: SummaryConfig | None = None,
    language: str | None = None,
) -> MeetingSummary:
    """Generate a structured interview evaluation from transcript text.

    Args:
        transcript_text: The plain-text transcript (as produced by
            Transcript.to_text()).
        config: Summary configuration. Uses defaults if not provided.
        language: Language code of the transcript (e.g. "de", "fa").
            When provided (and not "en"), the LLM is instructed to
            write the evaluation in that language.

    Returns:
        MeetingSummary with the Markdown evaluation, model used, and timing.

    Raises:
        ConnectionError: If Ollama is not reachable.
        RuntimeError: If the model fails to generate a response.
    """
    import time

    if config is None:
        config = SummaryConfig()

    if not is_ollama_available(config.ollama_url):
        raise ConnectionError(
            f"Ollama is not running at {config.ollama_url}. "
            "Start it with: ollama serve"
        )

    system_prompt = _build_system_prompt(language)

    if language and language != "en":
        lang_name = _LANGUAGE_NAMES.get(language, language)
        user_tpl = _load_prompt_file("summary_user_lang.txt")
        user_prompt = user_tpl.format(language=lang_name, transcript=transcript_text)
    else:
        user_tpl = _load_prompt_file("summary_user.txt")
        user_prompt = user_tpl.format(transcript=transcript_text)

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "think": False,  # Disable thinking/reasoning for speed
        "options": {
            "temperature": config.temperature,
            "num_ctx": config.num_ctx,
            # Снижает уход модели в «чужой» жанр (диплом, статья) вместо рубрики
            "repeat_penalty": 1.12,
        },
    }

    url = f"{config.ollama_url}/api/chat"
    t0 = time.time()

    try:
        resp = requests.post(url, json=payload, timeout=config.timeout)
        resp.raise_for_status()
    except requests.Timeout:
        raise RuntimeError(
            f"Ollama timed out after {config.timeout}s. "
            f"The model '{config.model}' may be too large or slow. "
            "Try a smaller model with --summary-model."
        )
    except requests.HTTPError as e:
        raise RuntimeError(f"Ollama API error: {e}")

    elapsed = time.time() - t0
    data = resp.json()
    content = data.get("message", {}).get("content", "")

    if not content.strip():
        raise RuntimeError(
            f"Ollama returned an empty response. Model '{config.model}' may "
            "not be available. Check with: ollama list"
        )

    return MeetingSummary(
        markdown=content.strip(),
        model=config.model,
        elapsed_seconds=elapsed,
    )
