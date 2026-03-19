# Основные команды meetscribe

Точка входа: `meet` (после установки пакета). В разработке из клона:

```bash
uv run meet <команда> ...
```

Переменные окружения: `HF_TOKEN` (диаризация), при необходимости `HF_TOKEN` в `huggingface-cli login`.

---

## Проверка и устройства

| Команда | Назначение |
|---------|------------|
| `meet check` | Проверка ffmpeg, PulseAudio/PipeWire, whisperx, CUDA, HF_TOKEN |
| `meet devices` | Список аудиоисточников и метки по умолчанию |

---

## Запись

| Команда | Назначение |
|---------|------------|
| `meet record` | Только запись; после Ctrl+C — сохранение WAV |
| `meet run` | Запись → по Ctrl+C транскрипция + summary + PDF |
| `meet gui` | GTK-виджет: запись и тот же пайплайн после остановки |

Частые опции записи:

- `-o /path`, `--output-dir` — каталог для файлов
- `--filename`, `-f` — имя файла
- `--mic`, `--monitor` — источники (см. `meet devices`)
- `--virtual-sink` — изолированный sink «Meet-Capture»

---

## Транскрипция

```bash
meet transcribe /path/to/meeting.wav
```

Если передать **каталог** сессии, берётся первый `*.wav` внутри.

Частые опции:

| Опция | Описание |
|-------|----------|
| `-m`, `--model` | Whisper (по умолчанию `large-v3-turbo`) |
| `-l`, `--language` | `auto`, `en`, `de`, `fr`, `es`, `tr`, `fa`, … |
| `--device` | `cuda` или `cpu` |
| `--compute-type` | `float16`, `int8` |
| `-b`, `--batch-size` | Размер батча (меньше — меньше VRAM) |
| `--hf-token` | Токен HF (или env `HF_TOKEN`) |
| `--no-diarize` | Без диаризации |
| `--min-speakers` / `--max-speakers` | Подсказка числа спикеров |
| `--skip-alignment` | Без выравнивания по словам |
| `--no-summarize` | Без AI-summary |
| `--summary-model` | Модель Ollama для summary (по умолчанию `qwen3.5:9b`) |
| `-o`, `--output-dir` | Куда писать транскрипты (по умолчанию — рядом с WAV) |

---

## Модели выравнивания (wav2vec2)

```bash
meet download              # статус кэша по языкам
meet download de tr fa     # скачать для указанных кодов
meet download --all        # все поддерживаемые
```

---

## Подписи спикеров

```bash
meet label /path/to/session-dir
```

- `--no-audio` — без проигрывания клипов
- `--no-summary` — не вызывать Ollama для summary, только замена имён в существующем `.summary.md`

---

## Суммаризация только по тексту (Ollama)

```bash
meet summarize /path/to/transcript.txt
meet summarize transcript.txt -l de
meet summarize transcript.txt -o /other/dir --summary-model gemma3:12b
```

- `-l auto` (по умолчанию) — если рядом есть `<basename>.json` (как после `meet transcribe`), берётся поле `language` для промптов; иначе считается английский сценарий.
- `-o` / `--output-dir` — каталог для `<basename>.summary.md` (по умолчанию — рядом с `.txt`).

---

## Перевод транскрипта (Ollama)

```bash
meet translate /path/to/session-dir
meet translate /path/to/session-dir --to de
```

- `--summary-model` — модель Ollama (по умолчанию как у summary)

Результат: `<basename>.translation.<lang>.txt` в каталоге сессии.

---

## Summary и Ollama

- Summary и PDF после транскрипции включаются по умолчанию; отключить: `--no-summarize`.
- Другая модель: `--summary-model <имя>` (например `gemma3:12b`).
- Ollama должен быть запущен (`ollama serve`).

---

## Версия

```bash
meet --version
```

---

Подробности: [README.md](README.md), [REQUIREMENTS.md](REQUIREMENTS.md).
