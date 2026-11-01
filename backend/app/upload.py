from fastapi import APIRouter, UploadFile, File, HTTPException
from app.document_state import current_document
from app.rag import ingest

router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    stats = ingest(await file.read(), filename=file.filename)

    current_document["filename"] = file.filename
    current_document["total_chunks"] = stats["n_chunks"]

    return {
        "filename": file.filename,
        "characters": stats["characters"],
        "total_chunks": stats["n_chunks"],
        "stored": True
    }
