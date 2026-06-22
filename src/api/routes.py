from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import shutil
import os
from src.models.document import Document, DocumentResponse
from src.services.document_processor import processor

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Nahraje soubor (PDF, PNG, JPG), uloží ho a spustí jeho zpracování na pozadí.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Uložíme soubor na disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Vytvoříme záznam o dokumentu
    doc = Document(filename=file.filename, filepath=file_path)
    processor.save_document(doc)

    # Spustíme zpracování na pozadí
    background_tasks.add_task(processor.process_document_async, doc.id)

    # Vrátíme ihned odpověď (aby klient nemusel čekat na OCR)
    return doc

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document_status(doc_id: str):
    """
    Vrátí aktuální stav zpracování dokumentu a případně vytěžená data.
    """
    doc = processor.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nebyl nalezen")
    
    return doc
