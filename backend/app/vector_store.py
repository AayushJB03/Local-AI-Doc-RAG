import chromadb

client = chromadb.PersistentClient(path="chroma_db")

# kept for the scratch test_*.py scripts; app code goes through the functions below
collection = client.get_or_create_collection(name="documents")


def store_chunks(chunks, embeddings, filename, collection_name="documents", ids=None):
    col = client.get_or_create_collection(name=collection_name)

    # ids include the doc name so the same chunk is identifiable across runs
    ids = ids or [f"{filename}::{i}" for i in range(len(chunks))]

    metadata = [
        {"filename": filename, "chunk_number": i}
        for i in range(len(chunks))
    ]

    col.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadata
    )


def retrieve_chunks(question_embedding, n_results=5, collection_name="documents"):
    col = client.get_or_create_collection(name=collection_name)

    results = col.query(
        query_embeddings=[question_embedding],
        n_results=n_results
    )

    return {
        "ids": results["ids"][0],
        "documents": results["documents"][0],
        "metadata": results["metadatas"][0]
    }


def clear_collection(collection_name="documents"):
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass  # didn't exist yet

    client.get_or_create_collection(name=collection_name)
