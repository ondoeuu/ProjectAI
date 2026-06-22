import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import re

# ==========================================
# 1. DATOVÉ MODELY (Pydantic)
# ==========================================

class Intent(BaseModel):
    founder_id: str
    company_name: str
    business_area: str
    expected_turnover: float
    company_type: str = "s.r.o."

class Duty(BaseModel):
    title: str
    description: str
    deadline: str
    is_immediate: bool = False

class Requirement(BaseModel):
    title: str
    description: str

class Proposal(BaseModel):
    """
    Klíčová struktura: Agent nejedná bez potvrzení. Vždy vrací Proposal (Podklad),
    který musí člověk zkontrolovat a potvrdit.
    """
    founder_id: str
    status: str = Field(description="Může být 'READY_FOR_REVIEW', 'MISSING_DATA'")
    company_name: str
    business_area: str
    immediate_duties: List[Duty] = []
    scheduled_duties: List[Duty] = []
    requirements: List[Requirement] = []
    founder_questions: List[str] = []
    explanation: str = Field(description="Lidsky čitelné vysvětlení toho, co agent zjistil a navrhuje.")

class OnboardRequest(BaseModel):
    intent_text: str

# ==========================================
# 2. MOCK ROZHRANÍ (API Sběrače dat)
# ==========================================

def get_intent(founder_id: str, intent_text: str) -> dict:
    """Vrátí počáteční záměr zakladatele na základě zadání z frontendu."""
    # Extrakce názvu firmy a typu živnosti z volného textu (simulace AI porozumění)
    company_name = "Nová firma s.r.o."
    business_area = "Volná živnost"
    
    if "Kofíčko" in intent_text:
        company_name = "Kofíčko s.r.o."
        business_area = "Hostinská činnost"
    elif "Inovace" in intent_text:
        company_name = "Inovace s.r.o."
        business_area = "Vývoj software"
    else:
        # Jednoduchý regex pro jakýkoliv název typu "Něco s.r.o."
        match = re.search(r'([A-ZŽŠČŘĎŤŇ][a-zžščřďťň]+\s+s\.r\.o\.)', intent_text)
        if match:
            company_name = match.group(1)

    return {
        "founder_id": founder_id,
        "company_name": company_name,
        "business_area": business_area,
        "expected_turnover": 1500000.0,
        "company_type": "s.r.o."
    }

def lookup_registry(query: dict) -> dict:
    """Sáhne do registrů (ARES, Živnostenský rejstřík, ROS) pro údaje."""
    if query.get("type") == "person":
        return {"found": True, "address": "Dlouhá 15, Praha", "birth_date": "1990-01-01"}
    elif query.get("type") == "company_name":
        # Ověření volnosti jména (simulace)
        name = query.get("name")
        if name == "Inovace s.r.o." or name == "Kofíčko s.r.o." or "Nová" in name or "s.r.o." in name:
            return {"available": True}
        return {"available": False}
    return {"found": False}

def lookup_legislation(tema: str) -> str:
    """Získá relevantní pravidla pro daný obor z platné legislativy."""
    if "software" in tema.lower():
        return "Obor: Vývoj software. Typ živnosti: Volná. Nejsou vyžadovány žádné speciální koncese ani prokazování praxe."
    elif "restaurace" in tema.lower() or "hostinská" in tema.lower():
        return "Obor: Hostinská činnost. Typ živnosti: Řemeslná. Vyžaduje prokázání odborné způsobilosti (vyučení v oboru nebo praxe)."
    return "Živnost volná, bez speciálních požadavků."

def schedule(founder_id: str, povinnost: str, termin: str) -> bool:
    print(f"[KALENDÁŘ] Naplánováno pro {founder_id}: {povinnost} na termín {termin}")
    return True

def ask_founder(founder_id: str, otazka: str) -> str:
    print(f"[DOTAZ NA ZAKLADATELE {founder_id}]: {otazka}")
    return "User response placeholder"

# ==========================================
# 3. MOZEK (Logika agenta)
# ==========================================

class TierOneAgent:
    def __init__(self):
        pass
        
    def onboard_company(self, founder_id: str, intent_text: str) -> Proposal:
        intent_data = get_intent(founder_id, intent_text)
        intent = Intent(**intent_data)
        
        proposal = Proposal(
            founder_id=founder_id,
            status="DRAFT",
            company_name=intent.company_name,
            business_area=intent.business_area,
            explanation=""
        )

        registry_person = lookup_registry({"type": "person", "name": "Jan Novák"})
        if not registry_person.get("found"):
            question = "Nenašli jsme vaše kompletní údaje v registru obyvatel. Prosím, doplňte své trvalé bydliště a datum narození."
            ask_founder(founder_id, question)
            proposal.status = "MISSING_DATA"
            proposal.founder_questions.append(question)
            proposal.explanation = "Pro pokračování potřebujeme doplnit chybějící osobní údaje."
            return proposal

        registry_company = lookup_registry({"type": "company_name", "name": intent.company_name})
        if not registry_company.get("available"):
            question = f"Název firmy '{intent.company_name}' je již obsazen. Jaký jiný název chcete použít?"
            ask_founder(founder_id, question)
            proposal.status = "MISSING_DATA"
            proposal.founder_questions.append(question)
            proposal.explanation = "Název firmy koliduje s existujícím subjektem. Navrhněte prosím jiný název."
            return proposal

        leg_info = lookup_legislation(intent.business_area)
        
        if "Řemeslná" in leg_info or "Koncesovaná" in leg_info:
            proposal.requirements.append(
                Requirement(
                    title="Doložení odborné způsobilosti", 
                    description=f"Pro obor '{intent.business_area}' legislativa vyžaduje doložení praxe nebo vzdělání. Důvod: {leg_info}"
                )
            )
        else:
            proposal.requirements.append(
                Requirement(
                    title="Ohlášení volné živnosti", 
                    description=f"Pro obor '{intent.business_area}' není vyžadována koncese. Postačuje ohlášení."
                )
            )

        proposal.immediate_duties.extend([
            Duty(
                title="Registrace k dani z příjmů (DPPO)",
                description="Povinná registrace do 15 dnů od vzniku.",
                deadline=(datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
                is_immediate=True
            ),
            Duty(
                title="Zápis do evidence skutečných majitelů (ESM)",
                description="Návrh na zápis musí být podán bez zbytečného odkladu.",
                deadline="Bez zbytečného odkladu",
                is_immediate=True
            )
        ])
        
        # Připojíme rovnou i scheduled duties pro účely dema
        proposal.scheduled_duties = self.schedule_public_duties(founder_id, {"type": "s.r.o."})

        proposal.status = "READY_FOR_REVIEW"
        proposal.explanation = (
            f"Všechny dostupné registry byly zkontrolovány. Název firmy '{intent.company_name}' je volný. "
            f"Připravil jsem návrh na založení a seznam povinných podkladů i okamžitých povinností po zápisu do OR."
        )

        return proposal

    def schedule_public_duties(self, founder_id: str, company_data: dict) -> List[Duty]:
        current_year = datetime.now().year
        return [
            Duty(
                title="Podání daňového přiznání (DPPO)",
                description="Elektronické podání přiznání.",
                deadline=f"{current_year + 1}-05-02"
            ),
            Duty(
                title="Založení účetní závěrky do sbírky listin",
                description="Zveřejnění účetní závěrky v OR.",
                deadline=f"{current_year + 1}-07-31" 
            )
        ]

# ==========================================
# 4. FASTAPI SERVER PRO FRONTEND
# ==========================================

app = FastAPI(title="eGov AI Agent API")

# Povolení CORS pro volání z frontendu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TierOneAgent()

@app.post("/api/onboard", response_model=Proposal)
def api_onboard(request: OnboardRequest):
    """
    Tento endpoint přijme text od uživatele a vrátí plnohodnotný Proposal 
    zpracovaný reálnou Python logikou Tier 1 Agenta.
    """
    founder_id = "user_bankid_123" # Simulace identity z přihlášení
    proposal = agent.onboard_company(founder_id=founder_id, intent_text=request.intent_text)
    return proposal

# Servírování statických souborů (Frontend)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    print("Startuji FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
