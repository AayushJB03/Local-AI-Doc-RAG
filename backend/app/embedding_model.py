from functools import lru_cache

from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=None)
def get_model(name=DEFAULT_MODEL):
    return SentenceTransformer(name)


model = get_model()
