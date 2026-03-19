"""MeetScribe — local meeting transcription with speaker diarization."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from cwd or project root so HF_TOKEN etc. are available
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# On Windows without Developer Mode, HuggingFace Hub fails with WinError 1314 when
# creating symlinks. Force copy-based cache to avoid OSError.
if os.name == "nt":
    import huggingface_hub.file_download as _hf_fd

    _orig_are_symlinks_supported = _hf_fd.are_symlinks_supported

    def _are_symlinks_supported_noop(cache_dir=None):
        return False

    _hf_fd.are_symlinks_supported = _are_symlinks_supported_noop
