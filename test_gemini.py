import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')
prompt = """
Jsi špičkový AI asistent pro zakládání firem.
Z následujícího textu extrahuj:
1) Název firmy (pokud není přesně určen, vymysli nějaký velmi pěkný a výstižný končící na 's.r.o.').
2) Obor podnikání (specificky a profesionálně pojmenovaný).
Odpověz POUZE validním JSON objektem, nic jiného nepiš.
Struktura: {"company_name": "...", "business_area": "..."}

Text uživatele: "chci založit autoopravnu a.s."
"""
try:
    response = model.generate_content(prompt)
    print("RAW RESPONSE:", response.text)
    raw_text = response.text.replace('```json', '').replace('```', '').strip()
    data = json.loads(raw_text)
    print("PARSED JSON:", data)
except Exception as e:
    print("ERROR:", e)
