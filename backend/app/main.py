from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import ollama
import time
from app.session_store import sessions
from app.upload import router as upload_router
from app.vector_store import retrieve_chunks
from app.embedding_model import model
from app.document_state import current_document
from app.error_handler import global_exception_handler

app = FastAPI(
    title="Document Q&A API",
    description="RAG-based Document Question Answering using Qwen3, ChromaDB and FastAPI",
    version="1.0.0"

)

app.add_exception_handler(Exception, global_exception_handler)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include upload router
app.include_router(upload_router)


# -----------------------------
# Basic Endpoints
# -----------------------------
@app.get("/")
def home():
    return {"message": "Backend Running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/document-info")
def document_info():
    return current_document


# -----------------------------
# Chat Request Model
# -----------------------------
class ChatRequest(BaseModel):
    session_id: str
    question: str = Field(
        min_length=3,
        max_length=500
    )


# -----------------------------
# Chat Endpoint
# -----------------------------
@app.post("/chat")
def chat(request: ChatRequest):

    # -------------------------
    # Step 1: Generate Embedding
    # -------------------------
    start = time.time()

    query_embedding = model.encode(
        request.question
    ).tolist()

    print(f"Embedding Time: {time.time() - start:.3f} seconds")

    # -------------------------
    # Step 2: Retrieve Chunks
    # -------------------------
    start = time.time()

    retrieval_result = retrieve_chunks(query_embedding)

    print(f"Retrieval Time: {time.time() - start:.3f} seconds")

    retrieved_chunks = retrieval_result["documents"]
    retrieved_metadata = retrieval_result["metadata"]

    context = "\n\n".join(retrieved_chunks)
    
    history = sessions.get(request.session_id, [])
    history = history[-5:]
    conversation = ""

    for msg in history:
        conversation += f"""
User: {msg['question']}
Assistant: {msg['answer']}
"""
    # -------------------------
    # Step 3: Prompt
    # -------------------------
    prompt = f"""
You are a document question-answering assistant.

Use the previous conversation if it helps answer follow-up questions.

Previous Conversation:
{conversation}

Context:
{context}

Current Question:
{request.question}

Answer:
"""

    # -------------------------
    # Step 4: LLM
    # -------------------------
    start = time.time()

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": "You are a document question-answering assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={"num_ctx": 8192}  # default context is huge -> 16GB KV cache OOM
    )

    print(f"LLM Time: {time.time() - start:.3f} seconds")

    # -------------------------
    # Step 5: Return Response
    # -------------------------
    history.append({
    "question": request.question,
    "answer": response["message"]["content"]
})

    sessions[request.session_id] = history
    return {
        "answer": response["message"]["content"],
        "sources": retrieved_metadata
    }