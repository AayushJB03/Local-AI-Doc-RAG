from app.vector_store import store_chunks, collection
from app.embedding_model import model

chunks = [
    "FastAPI is a Python framework.",
    "ChromaDB stores vector embeddings.",
    "RAG combines retrieval and generation."
]

embeddings = model.encode(chunks).tolist()

store_chunks(chunks, embeddings)

print("Documents Stored:", collection.count())