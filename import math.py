import math
import re
from collections import Counter

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "if", "in", "into", "is", "it", "no", "not", "of", "on", "or",
    "such", "that", "the", "their", "then", "there", "these", "they",
    "this", "to", "was", "will", "with", "from", "so", "what", "which",
    "when", "where", "who", "whom", "why", "how", "can", "could",
    "should", "would", "may", "might", "must", "have", "has", "had",
    "do", "does", "did", "your", "yourself", "yours", "i", "me",
    "my", "mine", "we", "us", "our", "ours", "he", "him", "his",
    "she", "her", "hers", "them", "their", "theirs", "its", "itself",
    "than", "then", "too", "very"
}

WORD_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9]*\b")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def normalize_word(word: str) -> str:
    return word.lower()


def tokenize(text: str) -> list[str]:
    return [normalize_word(w) for w in WORD_RE.findall(text)]


def sentence_split(text: str) -> list[str]:
    sentences = SENTENCE_RE.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]


def build_frequency_distribution(words: list[str]) -> Counter:
    filtered = [w for w in words if w not in STOPWORDS]
    return Counter(filtered)


def score_sentence(sentence: str, freq: Counter) -> float:
    words = tokenize(sentence)
    if not words:
        return 0.0
    score = 0.0
    for word in words:
        score += freq.get(word, 0)
    return score / math.sqrt(len(words))


def extract_key_sentences(text: str, top_n: int = 3) -> list[str]:
    sentences = sentence_split(text)
    if not sentences:
        return []
    words = tokenize(text)
    freq = build_frequency_distribution(words)
    scored = [(score_sentence(sentence, freq), index, sentence) for index, sentence in enumerate(sentences)]
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return [sentence for _, _, sentence in scored[:top_n]]


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    freq = build_frequency_distribution(tokenize(text))
    return [word for word, _ in freq.most_common(top_n)]


if __name__ == "__main__":
    example = (
        "Natural language processing enables machines to understand text. "
        "A simple key point extraction algorithm scores sentences by keyword frequency. "
        "Extracting key points helps summarize documents quickly. "
        "The algorithm ignores common stopwords and ranks sentences with significant terms."
    )

    print("Keywords:", extract_keywords(example, top_n=5))
    print("Key sentences:")
    for sentence in extract_key_sentences(example, top_n=3):
        print("-", sentence)
