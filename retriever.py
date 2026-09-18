import re
import math
from collections import Counter

from database import get_chunks


STOP_WORDS = {
    "the", "is", "a", "an", "of", "to",
    "in", "on", "for", "and", "or",
    "what", "why", "how", "are", "was",
    "were", "with", "from", "this",
    "that", "which", "can", "be"
}


def tokenize(text):
    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


def score_chunk(query, content):
    query_words = tokenize(query)
    content_words = tokenize(content)

    if not query_words or not content_words:
        return 0

    query_count = Counter(query_words)
    content_count = Counter(content_words)

    score = 0

    for word, q_count in query_count.items():

        if word in content_count:

            score += (
                q_count *
                content_count[word]
            )

    # Exact phrase bonus
    if query.lower() in content.lower():
        score += 10

    # Individual important words bonus
    for word in query_words:
        if len(word) >= 6 and word in content.lower():
            score += 1

    return score


def retrieve(topic_id, query, top_k=6):
    chunks = get_chunks(topic_id)

    scored = []

    for chunk in chunks:

        score = score_chunk(
            query,
            chunk["content"]
        )

        scored.append({
            **chunk,
            "score": score
        })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # If query matching is weak, still return
    # topic-specific content.
    selected = scored[:top_k]

    return selected


def build_context(chunks):
    if not chunks:
        return "No relevant study material was found."

    parts = []

    for chunk in chunks:
        parts.append(
            f"[Page {chunk['page_number']}]\n"
            f"{chunk['content']}"
        )

    return "\n\n".join(parts)