"""Text normalization helpers for moderation inputs."""

import re
from typing import Tuple


CONTROL_CHARS = re.compile(r"[\r\n\t]+")
MULTISPACE = re.compile(r"\s{2,}")


def normalize_text(raw: str) -> str:
    """Basic normalization; extend with lang-detect and length caps."""
    cleaned = CONTROL_CHARS.sub(" ", raw)
    cleaned = MULTISPACE.sub(" ", cleaned)
    return cleaned.strip()


def compute_hash(normalized: str) -> str:
    """Placeholder for a stable content hash (e.g., SHA256)."""
    # TODO: implement SHA256/MD5 or chosen hash for idempotency keys
    raise NotImplementedError("Implement stable content hashing for idempotency.")