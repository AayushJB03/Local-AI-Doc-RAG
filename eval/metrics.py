"""Retrieval metrics. A chunk is a hit if it contains the gold evidence quote,
so scores survive changing chunk size (chunk ids would not)."""
import re
from difflib import SequenceMatcher


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def contains_evidence(chunk, quote, fuzzy=0.9):
    c, q = norm(chunk), norm(quote)
    if not q:
        return False
    if q in c:
        return True
    # ponytail: O(len(chunk)/step) windows; swap for rapidfuzz if eval gets slow
    step = max(1, len(q) // 4)
    nums = re.findall(r"\d+(?:\.\d+)?", q)
    for i in range(0, max(1, len(c) - len(q) + 1), step):
        w = c[i:i + len(q)]
        # numbers must match exactly: 0.003 vs 0.004 is a different fact, not a typo
        if re.findall(r"\d+(?:\.\d+)?", w) == nums and SequenceMatcher(None, w, q).ratio() > fuzzy:
            return True
    return False


def first_hit_rank(chunks, quote):
    """1-based rank of first chunk containing the quote, or None."""
    for i, ch in enumerate(chunks, 1):
        if contains_evidence(ch, quote):
            return i
    return None


def hit_at_k(ranks, k):
    return sum(r is not None and r <= k for r in ranks) / len(ranks)


def mrr(ranks):
    return sum(1 / r for r in ranks if r) / len(ranks)


def percentile(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(p / 100 * (len(xs) - 1)))]


if __name__ == "__main__":
    quote = "The learning rate used for training was 0.003."
    chunks = ["unrelated text", "The  learning rate used for\ntraining was 0.003. More", "x"]
    assert first_hit_rank(chunks, quote) == 2          # whitespace-normalised hit
    assert first_hit_rank(["The learning rate used for training was 0.004."], quote) is None  # wrong number
    assert first_hit_rank(["The learning rate used for trainin was 0.003."], quote) == 1  # typo -> fuzzy hit
    assert first_hit_rank(["nothing relevant at all here"], quote) is None
    ranks = [1, 2, None, 5]
    assert hit_at_k(ranks, 1) == 0.25 and hit_at_k(ranks, 5) == 0.75
    assert abs(mrr(ranks) - (1 + .5 + .2) / 4) < 1e-9
    assert percentile([1, 2, 3, 4, 100], 50) == 3
    print("metrics ok")
