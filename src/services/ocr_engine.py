import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import os

class OCREngine:
    def __init__(self, lang="ces"):
        """
        Iniciuje OCR Engine. Defaultní jazyk je čeština.
        """
        self.lang = lang

    def extract_text_from_image(self, image_path: str) -> str:
        """
        Použije Tesseract k přečtení textu z obrázku (PNG, JPEG, atd.).
        """
        try:
            image = Image.open(image_path)
            # Tesseract musí být nainstalován v systému.
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            print(f"Chyba při OCR z obrázku: {e}")
            # V případě chybějícího Tesseractu v systému pro testování vrátíme dummy data
            return "DUMMY TEXT: Chyba OCR. Zkontrolujte, zda je nainstalován tesseract-ocr."

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Zkonvertuje PDF na obrázky a ty následně zpracuje OCR.
        """
        try:
            # Převede stránky PDF na list obrázků (Pillow Image objekty)
            # Vyžaduje nainstalovaný nástroj poppler v systému.
            images = convert_from_path(pdf_path)
            full_text = ""
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang=self.lang)
                full_text += f"\n--- Strana {i+1} ---\n{text}"
            return full_text
        except Exception as e:
            print(f"Chyba při OCR z PDF: {e}")
            return "DUMMY TEXT: Chyba zpracování PDF. Zkontrolujte, zda je nainstalován poppler."

    def process_file(self, file_path: str) -> str:
        """
        Hlavní metoda. Rozpozná formát podle přípony a spustí správný OCR proces.
        """
        _, ext = os.path.splitext(file_path.lower())
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Nepodporovaný formát souboru: {ext}")

ocr_engine = OCREngine()
