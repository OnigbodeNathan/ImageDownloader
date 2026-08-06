import re
from typing import List, Sequence


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "our",
    "that", "the", "their", "this", "to", "was", "were", "with", "will",
    "you", "your", "can"
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _split_into_sentences(text: str) -> List[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def _split_into_clauses(sentence: str) -> List[str]:
    parts = re.split(
        r"[,;:]|\b(?:and|or|but|while|because|when|so|if|although|though)\b",
        sentence,
        flags=re.IGNORECASE,
    )
    return [part.strip() for part in parts if part.strip()]


def _get_word_tokens(text: str) -> List[str]:
    return [word for word in re.sub(r"[^a-zA-Z0-9\s]", " ", text).split()]


def _score_candidate(text: str) -> int:
    words = [word.lower() for word in _get_word_tokens(text) if word.lower() not in STOP_WORDS and len(word) > 2]
    return sum(2 if len(word) > 5 else 1 for word in words)


def _extract_topic_phrases(clause: str) -> List[str]:
    words = _get_word_tokens(clause)
    phrases: List[str] = []
    run: List[str] = []
    for word in words:
        normalized = word.lower()
        if normalized not in STOP_WORDS and len(word) > 2:
            run.append(word)
        else:
            if len(run) >= 2:
                phrases.append(" ".join(run[:10]))
            run = []
    if len(run) >= 2:
        phrases.append(" ".join(run[:10]))
    return phrases


def extract_key_points(paragraph: str, max_words: int = 1000, top_n: int = 10) -> List[str]:
    """Extract topic phrases and sentential clauses from a paragraph into a short list.

    This extractor focuses on meaningful topics and clause-level highlights.
    It accepts up to max_words words, then returns the top_n most relevant items.
    """

    if not paragraph or not paragraph.strip():
        return []

    normalized = _normalize_text(paragraph)
    words = normalized.split()
    if len(words) > max_words:
        normalized = " ".join(words[:max_words])

    sentences = _split_into_sentences(normalized)
    if not sentences:
        return []

    scored_candidates: List[tuple[str, int]] = []
    for sentence in sentences:
        for clause in _split_into_clauses(sentence):
            clause_score = _score_candidate(clause)
            if clause_score >= 2:
                scored_candidates.append((clause.strip(), clause_score + min(3, len(_get_word_tokens(clause)))))
            for phrase in _extract_topic_phrases(clause):
                phrase_score = _score_candidate(phrase)
                if phrase_score >= 2:
                    scored_candidates.append((phrase.strip(), phrase_score + 1))

    if not scored_candidates:
        first_clause = _split_into_clauses(sentences[0])
        return [first_clause[0]] if first_clause else [_normalize_text(sentences[0])]

    scored_candidates.sort(key=lambda item: (-item[1], len(item[0])))

    result: List[str] = []
    seen = set()
    for text, _score in scored_candidates:
        key = text.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(text)
        if len(result) >= top_n:
            break

    return result


def extract_key_points_batch(texts: Sequence[str], max_words: int = 1000, top_n: int = 10) -> List[List[str]]:
    """Process multiple paragraphs or documents in batch and return a list of results."""
    return [extract_key_points(text, max_words=max_words, top_n=top_n) for text in texts]
