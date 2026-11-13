from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_accents.casefold().split())


def contains_term(normalized_text: str, term: str) -> bool:
    normalized_term = normalize_text(term)
    if " " in normalized_term:
        return normalized_term in normalized_text
    return re.search(
        rf"\b{re.escape(normalized_term)}\b",
        normalized_text,
    ) is not None
