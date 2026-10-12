# Document Q&A RAG System

## Features

- PDF Upload
- Text Extraction
- Chunking
- Embeddings
- ChromaDB Vector Database
- Retrieval-Augmented Generation (RAG)
- Qwen3 Integration
- FastAPI Backend

## Tech Stack

- FastAPI
- Qwen3
- Ollama
- ChromaDB
- Sentence Transformers
- LangChain Text Splitters

## Run

pip install -r requirements.txt

uvicorn app.main:app --reload

Open:
http://127.0.0.1:8000/docs