"""Conservative deterministic memory-candidate formation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from redstone.core.memory import MemoryType

_NOISE = re.compile(
    r"^(?:ok(?:ay)?|sure|thanks?|interesting|(?:that )?sounds good|let'?s see)[.! ]*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MemoryCandidate:
    content: str
    memory_type: MemoryType
    source: str
    project: str | None = None
    importance: float = 0.5


def reject_reason(candidate: MemoryCandidate) -> str | None:
    """Reject only obvious low-value conversational acknowledgements."""
    content = " ".join(candidate.content.split())
    if not content or _NOISE.fullmatch(content):
        return "low_value_noise"
    return None
