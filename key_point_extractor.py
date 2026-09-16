import re
from typing import List, Sequence


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "our",
    "that", "the", "their", "this", "to", "was", "were", "with", "will",
    "you", "your", "can", "use", "build", "testing", "find", "analyze",
    "improve", "expand", "automate"
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


def _content_words(text: str) -> List[str]:
    return [
        word.lower()
        for word in _get_word_tokens(text)
        if word.lower() not in STOP_WORDS and len(word) > 2
    ]


def _score_candidate(text: str) -> float:
    words = _content_words(text)
    if not words:
        return 0.0
    long_word_bonus = sum(1.5 if len(word) > 5 else 1 for word in words)
    phrase_bonus = 2.0 if len(words) >= 2 else 0.0
    context_penalty = 2.0 if re.match(r"^(it|this|that|they|these|those)\b", text, re.IGNORECASE) else 0.0
    return long_word_bonus + phrase_bonus - context_penalty


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


def _default_top_n(sentence_count: int) -> int:
    if sentence_count <= 1:
        return 1
    if sentence_count <= 3:
        return 2
    if sentence_count <= 6:
        return 3
    return 4


def extract_key_points(paragraph: str, max_words: int = 1000, top_n: int | None = None) -> List[str]:
    """Extract topic phrases and sentential clauses from a paragraph into a short list.

    This extractor focuses on meaningful topics and clause-level highlights.
    When top_n is omitted, it returns roughly one result for every two sentences,
    capped at four. It accepts up to max_words words.
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
    result_limit = _default_top_n(len(sentences)) if top_n is None else max(1, top_n)

    scored_candidates: List[tuple[str, float, int]] = []
    for sentence_index, sentence in enumerate(sentences):
        sentence_context_penalty = (
            2.0
            if re.match(r"^(it|this|that|they|these|those)\b", sentence, re.IGNORECASE)
            else 0.0
        )
        for clause in _split_into_clauses(sentence):
            clause_text = clause.strip()
            content_word_count = len(_content_words(clause_text))
            clause_score = (
                _score_candidate(clause_text) - sentence_context_penalty
            ) / max(1.0, content_word_count ** 0.5)
            if clause_score >= 2 and content_word_count >= 2:
                scored_candidates.append(
                    (
                        clause_text,
                        clause_score,
                        sentence_index,
                    )
                )
            for phrase in _extract_topic_phrases(clause):
                phrase_score = _score_candidate(phrase)
                if phrase_score >= 2:
                    scored_candidates.append(
                        (
                            phrase.strip(),
                            phrase_score + 3.5 - sentence_context_penalty,
                            sentence_index,
                        )
                    )

    if not scored_candidates:
        first_clause = _split_into_clauses(sentences[0])
        return [first_clause[0]] if first_clause else [_normalize_text(sentences[0])]

    scored_candidates.sort(key=lambda item: (-item[1], len(item[0])))

    result: List[str] = []
    seen = set()
    used_sentences = set()
    for text, score, sentence_index in scored_candidates:
        key = text.lower().strip()
        if key and key not in seen and sentence_index not in used_sentences:
            seen.add(key)
            result.append(text)
            used_sentences.add(sentence_index)
        if len(result) >= result_limit:
            break

    if len(result) < result_limit:
        for text, _score, _sentence_index in scored_candidates:
            key = text.lower().strip()
            if key and key not in seen:
                seen.add(key)
                result.append(text)
            if len(result) >= result_limit:
                break

    return result


def extract_key_points_batch(
    texts: Sequence[str], max_words: int = 1000, top_n: int | None = None
) -> List[List[str]]:
    """Process multiple paragraphs or documents in batch and return a list of results."""
    return [extract_key_points(text, max_words=max_words, top_n=top_n) for text in texts]
