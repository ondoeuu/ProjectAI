import re
from src.models.document import ExtractedData

class DataExtractor:
    def __init__(self):
        # Regulární výrazy pro základní účetní data
        self.regex_ico = r'(?:IČO?|IČ)\s*:?\s*(\d{8})'
        self.regex_dic = r'(?:DIČ)\s*:?\s*(CZ\d{8,10})'
        # Hledá částky např. "1 500,00", "1500", "1500.00" v blízkosti slov jako celkem, k úhradě
        self.regex_total = r'(?:Celkem|K úhradě|Celková částka)[\s\w]*:?\s*(\d{1,3}(?:[ \.]\d{3})*(?:,\d{2})?)'
        # Datum formátu DD.MM.YYYY nebo D.M.YYYY
        self.regex_date = r'(?:Datum vystavení|Vystaveno)[\s\w]*:?\s*(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})'
        self.regex_due_date = r'(?:Splatnost|Datum splatnosti)[\s\w]*:?\s*(\d{1,2}\.\s?\d{1,2}\.\s?\d{4})'

    def extract(self, raw_text: str) -> ExtractedData:
        """
        Vyextrahuje strukturovaná data z hrubého textu.
        V budoucnu zde může být implementováno volání LLM (např. OpenAI API).
        """
        data = ExtractedData(raw_text=raw_text)
        
        # Hledání IČO
        ico_match = re.search(self.regex_ico, raw_text, re.IGNORECASE)
        if ico_match:
            data.ico = ico_match.group(1).replace(" ", "")

        # Hledání DIČ
        dic_match = re.search(self.regex_dic, raw_text, re.IGNORECASE)
        if dic_match:
            data.dic = dic_match.group(1).replace(" ", "")
            
        # Hledání data vystavení
        issue_match = re.search(self.regex_date, raw_text, re.IGNORECASE)
        if issue_match:
            data.issue_date = issue_match.group(1)
            
        # Hledání data splatnosti
        due_match = re.search(self.regex_due_date, raw_text, re.IGNORECASE)
        if due_match:
            data.due_date = due_match.group(1)
            
        # Hledání celkové částky (zjednodušené)
        amount_match = re.search(self.regex_total, raw_text, re.IGNORECASE)
        if amount_match:
            # Převedeme na float ("1 500,00" -> 1500.00)
            raw_amount = amount_match.group(1)
            clean_amount = raw_amount.replace(" ", "").replace(".", "").replace(",", ".")
            try:
                data.total_amount = float(clean_amount)
            except ValueError:
                pass # Extrakce selhala

        return data

extractor = DataExtractor()
