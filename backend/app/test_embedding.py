from app.embedding_model import model

embedding = model.encode(
    "Hello world"
)

print("Vector Length:", len(embedding))