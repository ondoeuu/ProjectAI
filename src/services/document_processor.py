import asyncio
from typing import Dict
from src.models.document import Document, DocumentStatus
from src.services.ocr_engine import ocr_engine
from src.services.data_extractor import extractor

class DocumentProcessor:
    def __init__(self):
        # Pro zjednodušení ukládáme dokumenty v paměti (in-memory DB).
        # V produkci by se použila relační databáze (SQLAlchemy -> PostgreSQL/SQLite).
        self.db: Dict[str, Document] = {}

    def save_document(self, doc: Document):
        self.db[doc.id] = doc

    def get_document(self, doc_id: str) -> Document:
        return self.db.get(doc_id)

    async def process_document_async(self, doc_id: str):
        """
        Asynchronní zpracování dokumentu (aby neblokovalo API).
        1. OCR (Získání textu)
        2. Extrakce strukturovaných dat
        """
        doc = self.get_document(doc_id)
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        self.save_document(doc)

        try:
            # 1. OCR Fáze (Může trvat déle)
            # Protože OCR je synchronní a blokující proces, měli bychom ho
            # v produkci spouštět v background thread poolu (např. přes run_in_executor)
            loop = asyncio.get_event_loop()
            raw_text = await loop.run_in_executor(None, ocr_engine.process_file, doc.filepath)
            
            doc.status = DocumentStatus.OCR_COMPLETED
            self.save_document(doc)

            # 2. Extrakce dat (rychlý regex proces)
            extracted = extractor.extract(raw_text)
            doc.extracted_data = extracted
            doc.status = DocumentStatus.EXTRACTION_COMPLETED
            self.save_document(doc)

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            self.save_document(doc)

processor = DocumentProcessor()
