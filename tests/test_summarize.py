"""Tests for meet.summarize — system prompt construction."""

from __future__ import annotations

from meet.summarize import _build_system_prompt
from meet.languages import LANG_NAMES as _LANG_NAMES


class TestBuildSystemPrompt:
    def test_english_default(self) -> None:
        prompt = _build_system_prompt("en")
        assert "эксперт по оценке кандидатов" in prompt
        assert "ОТВЕТСТВЕННОСТЬ" in prompt
        assert "КТО ОЦЕНИВАЕТСЯ" in prompt
        assert "СТРОГО ЗАПРЕЩЕНО" in prompt
        assert "ЯЗЫК ОТВЕТА" not in prompt

    def test_farsi_output_instruction(self) -> None:
        prompt = _build_system_prompt("fa")
        assert "Persian" in prompt or "Farsi" in prompt
        assert "ЯЗЫК ОТВЕТА" in prompt

    def test_all_supported_languages(self) -> None:
        """Known LANG_NAMES (non-en) append an output-language block."""
        for lang in _LANG_NAMES:
            prompt = _build_system_prompt(lang)
            assert "КРИТЕРИИ ОЦЕНКИ" in prompt
            if lang == "en":
                assert "ЯЗЫК ОТВЕТА" not in prompt
            else:
                assert _LANG_NAMES[lang] in prompt
                assert "ЯЗЫК ОТВЕТА" in prompt

    def test_unknown_language_no_extra_block(self) -> None:
        prompt = _build_system_prompt("xx")
        assert "эксперт по оценке кандидатов" in prompt
        assert "ЯЗЫК ОТВЕТА" not in prompt
