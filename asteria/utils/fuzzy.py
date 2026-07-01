"""
Fuzzy search utilities for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from typing import Any, Callable, TypeVar

from thefuzz import fuzz, process

from asteria.constants import FUZZY_SEARCH_THRESHOLD

logger = logging.getLogger("asteria.utils.fuzzy")

T = TypeVar("T")


def fuzzy_score(query: str, text: str) -> int:
    """Compute a fuzzy match score between query and text.

    Uses token set ratio for best results with out-of-order words.

    Args:
        query: Search query string.
        text: Target text to match against.

    Returns:
        Integer score between 0 and 100.
    """
    return fuzz.token_set_ratio(query.lower(), text.lower())


def fuzzy_filter(
    query: str,
    items: list[T],
    key: Callable[[T], str],
    threshold: int = FUZZY_SEARCH_THRESHOLD,
) -> list[tuple[T, int]]:
    """Filter a list of items by fuzzy match score.

    Args:
        query: Search query.
        items: List of items to search.
        key: Function to extract the search text from each item.
        threshold: Minimum score (0–100) to include a result.

    Returns:
        List of (item, score) tuples sorted by descending score.
    """
    if not query:
        return [(item, 100) for item in items]

    results: list[tuple[T, int]] = []
    for item in items:
        text = key(item)
        score = fuzzy_score(query, text)
        if score >= threshold:
            results.append((item, score))

    results.sort(key=lambda x: x[1], reverse=True)
    logger.debug(
        "Fuzzy search '%s' → %d results (threshold=%d)", query, len(results), threshold
    )
    return results


def fuzzy_search_dicts(
    query: str,
    records: list[dict[str, Any]],
    fields: list[str],
    threshold: int = FUZZY_SEARCH_THRESHOLD,
) -> list[dict[str, Any]]:
    """Fuzzy search across multiple fields of a list of dictionaries.

    Combines the text from all specified fields and scores each record.

    Args:
        query: Search query string.
        records: List of dictionary records.
        fields: List of field names to search within each record.
        threshold: Minimum combined score.

    Returns:
        Filtered list of matching records, ordered by score.
    """
    if not query:
        return records

    def combined_key(record: dict[str, Any]) -> str:
        parts = []
        for field in fields:
            value = record.get(field)
            if value:
                if isinstance(value, list):
                    parts.extend(str(v) for v in value)
                else:
                    parts.append(str(value))
        return " ".join(parts)

    results = fuzzy_filter(query, records, key=combined_key, threshold=threshold)
    return [item for item, _score in results]


def exact_or_fuzzy_match(
    query: str,
    items: list[T],
    key: Callable[[T], str],
    threshold: int = FUZZY_SEARCH_THRESHOLD,
) -> list[T]:
    """Return exact matches first, then fuzzy matches above threshold.

    Args:
        query: Search query.
        items: Items to search.
        key: Text extractor.
        threshold: Fuzzy threshold.

    Returns:
        Matched items with exact matches prioritised.
    """
    exact: list[T] = []
    fuzzy_results: list[tuple[T, int]] = []

    query_lower = query.lower()
    for item in items:
        text = key(item).lower()
        if query_lower in text:
            exact.append(item)
        else:
            score = fuzzy_score(query, key(item))
            if score >= threshold:
                fuzzy_results.append((item, score))

    fuzzy_results.sort(key=lambda x: x[1], reverse=True)
    seen_ids = {id(i) for i in exact}
    for item, _ in fuzzy_results:
        if id(item) not in seen_ids:
            exact.append(item)
    return exact
