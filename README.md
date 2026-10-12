# 📄 AI Document Q&A using RAG

An AI-powered Document Question Answering system built using **FastAPI**, **Angular**, **ChromaDB**, **Sentence Transformers**, and **Qwen (Ollama)**.

The application allows users to upload PDF documents and ask natural language questions. It retrieves the most relevant document chunks using Retrieval-Augmented Generation (RAG) and generates accurate answers using a local Large Language Model.

---

## 🚀 Features

- 📄 Upload PDF documents
- 🤖 Ask questions in natural language
- 🔍 Retrieval-Augmented Generation (RAG)
- 🧠 Local LLM using Qwen via Ollama
- 📚 ChromaDB Vector Database
- 🔗 Sentence Transformer Embeddings
- 💬 Multi-turn conversation support
- 📌 Source chunk references
- 📊 Document information
- ⚡ FastAPI REST API
- 🎨 Angular Frontend
- 🌐 CORS enabled

---

## 🛠 Tech Stack

### Backend
- Python
- FastAPI
- Ollama
- Qwen 4B
- ChromaDB
- Sentence Transformers

### Frontend
- Angular
- TypeScript
- HTML
- CSS

---

## 📂 Project Structure

```
AI-Document-QA-RAG/
│
├── backend/
│   ├── app/
│   ├── chroma_db/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── angular.json
│   └── README.md
│
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/Likitha3126/AI-Document-QA-RAG.git
```

### Backend

```bash
cd backend

python -m venv .venv

.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

### Frontend

```bash
cd frontend

npm install

ng serve
```

---

## 🌐 URLs

Frontend

```
http://localhost:4200
```

Backend

```
http://127.0.0.1:8000
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

## 📖 Workflow

1. Upload a PDF
2. Extract text
3. Split into chunks
4. Generate embeddings
5. Store embeddings in ChromaDB
6. Ask a question
7. Retrieve relevant chunks
8. Generate answer using Qwen
9. Display answer with source references

---


## 👩‍💻 Author

Likitha Udayagiri

Internship Project