import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = """
Jsi špičkový AI asistent pro zakládání firem.
Z následujícího textu extrahuj:
1) Název firmy PŘESNĚ tak, jak ho uživatel zadal (pouze přidej 's.r.o.', nebo 'a.s.', pokud chybí právní forma). Pokud uživatel jméno vůbec nezadá, vymysli nějaké výstižné. Nekreativni! Použij to, co uživatel napsal.
2) Obor podnikání (specificky a profesionálně pojmenovaný podle skutečných živností).
Odpověz POUZE validním JSON objektem, nic jiného nepiš.
Struktura: {"company_name": "...", "business_area": "..."}

Text uživatele: "cez a energetické firmy a co k ni potrebuju"
    """
    response = model.generate_content(prompt)
    print("RAW RESPONSE:", response.text)
    
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if match:
        raw_text = match.group(0)
        print("MATCHED TEXT:", raw_text)
        data = json.loads(raw_text)
        print("PARSED DATA:", data)
    else:
        print("NO MATCH IN RESPONSE")

except Exception as e:
    print(f"Gemini API Error: {e}")
