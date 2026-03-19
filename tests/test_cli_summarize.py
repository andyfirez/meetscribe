"""Tests for meet summarize (text file) CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from meet.cli import main
from meet.summarize import MeetingSummary


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_summarize_writes_summary_md(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    txt = tmp_path / "session.txt"
    txt.write_text("[00:00:01 --> 00:00:05] A: Hello world.\n", encoding="utf-8")

    def fake_summarize(
        transcript_text: str,
        config=None,
        language: str | None = None,
    ) -> MeetingSummary:
        assert "Hello world" in transcript_text
        assert language is None
        return MeetingSummary(markdown="## Overview\nTest.", model="m", elapsed_seconds=0.5)

    monkeypatch.setattr("meet.summarize.summarize", fake_summarize)
    monkeypatch.setattr("meet.summarize.is_ollama_available", lambda url="http://localhost:11434": True)

    result = runner.invoke(main, ["summarize", str(txt)])
    assert result.exit_code == 0
    out = tmp_path / "session.summary.md"
    assert out.read_text(encoding="utf-8") == "## Overview\nTest."
    assert "Summary saved:" in result.output


def test_summarize_language_from_sidecar_json(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    txt = tmp_path / "meet.txt"
    txt.write_text("Hallo", encoding="utf-8")
    (tmp_path / "meet.json").write_text(json.dumps({"language": "de"}), encoding="utf-8")

    seen: dict[str, str | None] = {}

    def fake_summarize(
        transcript_text: str,
        config=None,
        language: str | None = None,
    ) -> MeetingSummary:
        seen["language"] = language
        return MeetingSummary(markdown="x", model="m", elapsed_seconds=0.1)

    monkeypatch.setattr("meet.summarize.summarize", fake_summarize)
    monkeypatch.setattr("meet.summarize.is_ollama_available", lambda url="http://localhost:11434": True)

    result = runner.invoke(main, ["summarize", str(txt), "-l", "auto"])
    assert result.exit_code == 0
    assert seen["language"] == "de"


def test_summarize_explicit_language_overrides_auto(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    txt = tmp_path / "meet.txt"
    txt.write_text("Hi", encoding="utf-8")
    (tmp_path / "meet.json").write_text(json.dumps({"language": "de"}), encoding="utf-8")

    seen: dict[str, str | None] = {}

    def fake_summarize(
        transcript_text: str,
        config=None,
        language: str | None = None,
    ) -> MeetingSummary:
        seen["language"] = language
        return MeetingSummary(markdown="x", model="m", elapsed_seconds=0.1)

    monkeypatch.setattr("meet.summarize.summarize", fake_summarize)
    monkeypatch.setattr("meet.summarize.is_ollama_available", lambda url="http://localhost:11434": True)

    result = runner.invoke(main, ["summarize", str(txt), "-l", "fr"])
    assert result.exit_code == 0
    assert seen["language"] == "fr"


def test_summarize_empty_file_exits_error(runner: CliRunner, tmp_path: Path) -> None:
    txt = tmp_path / "empty.txt"
    txt.write_text("   \n", encoding="utf-8")
    result = runner.invoke(main, ["summarize", str(txt)])
    assert result.exit_code == 1
    assert "empty" in result.output.lower()


def test_summarize_no_ollama_exits_error(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    txt = tmp_path / "t.txt"
    txt.write_text("Some text", encoding="utf-8")
    monkeypatch.setattr("meet.summarize.is_ollama_available", lambda url="http://localhost:11434": False)
    result = runner.invoke(main, ["summarize", str(txt)])
    assert result.exit_code == 1
    assert "ollama" in result.output.lower()


def test_summarize_custom_output_dir(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    txt = tmp_path / "sub" / "a.txt"
    txt.parent.mkdir(parents=True)
    txt.write_text("Body", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    monkeypatch.setattr(
        "meet.summarize.summarize",
        lambda *a, **k: MeetingSummary(markdown="m", model="x", elapsed_seconds=0.0),
    )
    monkeypatch.setattr("meet.summarize.is_ollama_available", lambda url="http://localhost:11434": True)

    result = runner.invoke(main, ["summarize", str(txt), "-o", str(out_dir)])
    assert result.exit_code == 0
    assert (out_dir / "a.summary.md").read_text(encoding="utf-8") == "m"
