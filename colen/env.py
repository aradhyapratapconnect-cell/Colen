"""Load environment variables from a project-local ``.env`` file.

Colen reads its configuration (API keys, endpoints, voice settings) from
plain environment variables.  To keep secrets out of source control they can
instead live in a ``.env`` file placed in the current working directory or in
the project root::

    GROQ_API_KEY=gsk_...
    COLEN_TTS_URL=http://localhost:8000/tts

The loader is dependency-free, ignores malformed lines, and never overrides
variables that are already set in the real environment (shell exports win).
``.env`` is git-ignored; ``.env.example`` documents every supported key.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILENAME = ".env"


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    """Return a ``(key, value)`` pair for a ``KEY=VALUE`` line, else ``None``."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export "):].lstrip()
    if "=" not in line:
        return None
    key, _, value = line.partition("=")
    key = key.strip()
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    if not key:
        return None
    return key, value


def load_env(path: Optional[str] = None, override: bool = False) -> Optional[Path]:
    """Load ``KEY=VALUE`` pairs from a ``.env`` file into ``os.environ``.

    Resolution order when *path* is not given: ``./.env`` (current working
    directory) first, then the project root's ``.env``.  Existing environment
    variables are left untouched unless *override* is true.

    Returns the path that was loaded, or ``None`` if no ``.env`` exists.
    """
    if path is None:
        candidates = [Path.cwd() / ENV_FILENAME, PROJECT_ROOT / ENV_FILENAME]
        env_path = next((p for p in candidates if p.is_file()), None)
        if env_path is None:
            return None
    else:
        env_path = Path(path)
        if not env_path.is_file():
            return None

    try:
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return None

    for line in lines:
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        if override or key not in os.environ:
            os.environ[key] = value
    return env_path
