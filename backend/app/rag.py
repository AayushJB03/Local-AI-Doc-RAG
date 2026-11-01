"""RAG pipeline as plain functions: no HTTP, every knob a parameter."""
import io
import os
import time

import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.embedding_model import get_model, DEFAULT_MODEL
from app.vector_store import store_chunks, retrieve_chunks, clear_collection

PROMPTS = {
    "v1": """
You are a document question-answering assistant.

Use the previous conversation if it helps answer follow-up questions.

Previous Conversation:
{conversation}

Context:
{context}

Current Question:
{question}

Answer:
""",
}


def extract_text(pdf):
    """pdf: path or raw bytes."""
    src = io.BytesIO(pdf) if isinstance(pdf, bytes) else pdf
    text = ""
    for page in PdfReader(src).pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted
    return text


def ingest(pdf, filename=None, chunk_size=500, overlap=100,
           collection_name="documents", embedding_model=DEFAULT_MODEL):
    """Chunk, embed and store a PDF (path or bytes), replacing the collection. Returns stats."""
    filename = filename or os.path.basename(pdf)
    text = extract_text(pdf)

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = splitter.split_text(text)

    clear_collection(collection_name)
    embeddings = get_model(embedding_model).encode(chunks).tolist()
    store_chunks(chunks, embeddings, filename, collection_name)

    return {"filename": filename, "characters": len(text), "n_chunks": len(chunks)}


def retrieve(question, k=5, collection_name="documents", embedding_model=DEFAULT_MODEL):
    """Returns ids, documents, metadata plus embed/retrieve timings in ms."""
    t0 = time.perf_counter()
    q_emb = get_model(embedding_model).encode(question).tolist()
    t1 = time.perf_counter()
    result = retrieve_chunks(q_emb, n_results=k, collection_name=collection_name)
    t2 = time.perf_counter()

    result["embed_ms"] = (t1 - t0) * 1000
    result["retrieve_ms"] = (t2 - t1) * 1000
    return result


def answer(question, chunks, prompt_version="v1", model="qwen3:4b", history=None):
    """history: list of {question, answer}. Returns text, token counts and llm_ms."""
    conversation = ""
    for msg in history or []:
        conversation += f"""
User: {msg['question']}
Assistant: {msg['answer']}
"""
    prompt = PROMPTS[prompt_version].format(
        conversation=conversation,
        context="\n\n".join(chunks),
        question=question,
    )

    t0 = time.perf_counter()
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": "You are a document question-answering assistant."},
            {"role": "user", "content": prompt},
        ],
        options={"num_ctx": 8192},  # default context is huge -> 16GB KV cache OOM
    )
    wall_ms = (time.perf_counter() - t0) * 1000

    return {
        "text": response["message"]["content"],
        "prompt_tokens": response.get("prompt_eval_count"),
        "completion_tokens": response.get("eval_count"),
        "llm_ms": wall_ms,
    }


def ask(question, k=5, collection_name="documents", embedding_model=DEFAULT_MODEL,
        prompt_version="v1", model="qwen3:4b", history=None):
    r = retrieve(question, k, collection_name, embedding_model)
    a = answer(question, r["documents"], prompt_version, model, history)

    return {
        "answer": a["text"],
        "chunks": r["documents"],
        "chunk_ids": r["ids"],
        "metadata": r["metadata"],
        "latency_ms": {"embed": r["embed_ms"], "retrieve": r["retrieve_ms"], "llm": a["llm_ms"]},
        "tokens": {"prompt": a["prompt_tokens"], "completion": a["completion_tokens"]},
    }
