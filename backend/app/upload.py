from fastapi import APIRouter, UploadFile, File
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import io
from fastapi import HTTPException
from app.document_state import current_document
from app.vector_store import (
    store_chunks,
    clear_collection
)

router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
        status_code=400,
        detail="Only PDF files are allowed."
    )
    # Read uploaded PDF
    pdf_bytes = await file.read()

    # Open PDF
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

    # Extract text from all pages
    text = ""

    for page in pdf_reader.pages:
        extracted = page.extract_text()

        if extracted:
            text += extracted

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)
    from app.embedding_model import model
    from app.vector_store import store_chunks

    clear_collection()

    # Generate embeddings for the chunks
    embeddings = model.encode(chunks).tolist()

    # Store the chunks and their embeddings
    store_chunks(
    chunks,
    embeddings,
    file.filename
)
    current_document["filename"] = file.filename
    current_document["total_chunks"] = len(chunks)

    # Return information about chunks
    return {
    "filename": file.filename,
    "characters": len(text),
    "total_chunks": len(chunks),
    "stored": True
}