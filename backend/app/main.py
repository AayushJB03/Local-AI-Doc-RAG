from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.session_store import sessions
from app.upload import router as upload_router
from app.rag import ask
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
    history = sessions.get(request.session_id, [])[-5:]

    result = ask(request.question, history=history)
    print(f"Latency ms: {result['latency_ms']} Tokens: {result['tokens']}")

    history.append({
        "question": request.question,
        "answer": result["answer"]
    })
    sessions[request.session_id] = history

    return {
        "answer": result["answer"],
        "sources": result["metadata"]
    }
