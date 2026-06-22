from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class DocumentStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    FAILED = "FAILED"

class ExtractedData(BaseModel):
    ico: Optional[str] = Field(None, description="IČO (Identifikační číslo osoby) dodavatele")
    dic: Optional[str] = Field(None, description="DIČ (Daňové identifikační číslo) dodavatele")
    total_amount: Optional[float] = Field(None, description="Celková částka na dokumentu")
    currency: Optional[str] = Field(None, description="Měna, např. CZK, EUR")
    issue_date: Optional[str] = Field(None, description="Datum vystavení")
    due_date: Optional[str] = Field(None, description="Datum splatnosti")
    raw_text: Optional[str] = Field(None, description="Hrubý text extrahovaný pomocí OCR")

class DocumentCreate(BaseModel):
    filename: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: DocumentStatus
    created_at: datetime
    extracted_data: Optional[ExtractedData] = None
    error_message: Optional[str] = None

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    filepath: str
    status: DocumentStatus = DocumentStatus.RECEIVED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_data: ExtractedData = Field(default_factory=ExtractedData)
    error_message: Optional[str] = None
