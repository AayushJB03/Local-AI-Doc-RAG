from app.vector_store import collection
from app.embedding_model import model

question = "What is FastAPI?"

query_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=2
)

print(results["documents"])