from __future__ import annotations

import contextlib
import logging
import re
import sys
from logging.handlers import RotatingFileHandler

from .config import Settings

SECRET_PATTERNS = (
    re.compile(r"\b(?:gsk|sk)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bmfa\.[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"(?i)\b(?:discord_token|groq_api_key|openai_api_key)\s*=\s*[^\s'\"]+"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._-]{16,}"),
)


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern in SECRET_PATTERNS:
            message = pattern.sub(lambda match: _replacement(match), message)
        return message


class _DiscordNoiseFilter(logging.Filter):
    """Drop unactionable discord.py warnings: no voice, no guild state by design.

    This bot only reads authorized DMs, so voice-dependency warnings and the
    guilds-intent notice are expected, not problems.
    """

    PATTERN = re.compile(
        r"PyNaCl|davey|voice will NOT be supported|Guilds intent seems to be disabled",
        re.IGNORECASE,
    )

    def filter(self, record: logging.LogRecord) -> bool:
        return not (
            record.name.startswith("discord.") and self.PATTERN.search(record.getMessage() or "")
        )


def configure_logging(settings: Settings) -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        settings.log_dir.chmod(0o700)
    level = getattr(logging, settings.log_level, logging.INFO)
    formatter = RedactingFormatter(
        "%(asctime)s %(levelname)-7s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    voice_filter = _DiscordNoiseFilter()
    stderr = logging.StreamHandler(sys.stderr)
    stderr.setFormatter(formatter)
    stderr.addFilter(voice_filter)
    file_handler = RotatingFileHandler(
        settings.log_dir / "voicebot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(voice_filter)
    with contextlib.suppress(OSError):
        (settings.log_dir / "voicebot.log").chmod(0o600)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(stderr)
    root.addHandler(file_handler)
    # discord.py is chatty at INFO (login, gateway sessions); warnings+ carry the signal.
    logging.getLogger("discord").setLevel(max(level, logging.WARNING))


def _replacement(match: re.Match[str]) -> str:
    text = match.group(0)
    lowered = text.lower()
    if lowered.startswith("authorization:"):
        return match.group(1) + "<redacted>"
    if lowered.startswith("bearer "):
        return match.group(1) + "<redacted>"
    if "=" in text:
        key, _, _ = text.partition("=")
        return f"{key.strip()}=<redacted>"
    return "<redacted>"
