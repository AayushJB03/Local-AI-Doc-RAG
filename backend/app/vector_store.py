import chromadb

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)


def store_chunks(chunks, embeddings, filename):

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    metadata = [
    {
        "filename": filename,
        "chunk_number": i
    }
    for i in range(len(chunks))
]

    collection.add(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadata
)

def retrieve_chunks(question_embedding, n_results=5):

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results
    )

    return {
    "documents": results["documents"][0],
    "metadata": results["metadatas"][0]
}
def clear_collection():
    global collection

    client.delete_collection("documents")

    collection = client.get_or_create_collection(
        name="documents"
    )