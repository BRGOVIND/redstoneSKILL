"""Conservative local privacy policy."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", re.IGNORECASE),
    "authorization": re.compile(r"\b(?:bearer|basic)\s+[a-z0-9._~+/=-]{12,}\b", re.IGNORECASE),
    "api_key": re.compile(r"\b(?:sk|rk|pk|ghp)_[a-zA-Z0-9_-]{16,}\b"),
    "password_assignment": re.compile(
        r"\b(?:password|passwd|secret)\s*[:=]\s*\S{8,}", re.IGNORECASE
    ),
}


@dataclass(frozen=True)
class PrivacyFinding:
    """A detected secret-like value; never exposes the matched value."""

    kind: str


class PrivacyPolicy:
    """Blocks likely credentials before they enter persistent storage."""

    def scan(self, text: str) -> list[PrivacyFinding]:
        return [
            PrivacyFinding(kind)
            for kind, pattern in _SECRET_PATTERNS.items()
            if pattern.search(text)
        ]

    def ensure_storable(self, text: str) -> None:
        findings = self.scan(text)
        if findings:
            kinds = ", ".join(finding.kind for finding in findings)
            raise ValueError(f"memory rejected by privacy policy: {kinds}")
