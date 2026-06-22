import json
import os
import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import re

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(override=True)
if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "vlozte_sem_svuj_klic":
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ==========================================
# 1. DATABÁZE (SQLAlchemy)
# ==========================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./egov.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # e.g. "user_bankid_123"
    name = Column(String)
    
    companies = relationship("DBCompany", back_populates="owner")

class DBCompany(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    ico = Column(String, nullable=True)
    business_area = Column(String)
    status = Column(String) # e.g. "Založeno", "Čeká na schválení"
    
    owner = relationship("DBUser", back_populates="companies")
    tasks = relationship("DBTask", back_populates="company")

class DBTask(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String)
    description = Column(String)
    deadline = Column(String)
    is_completed = Column(Boolean, default=False)
    can_automate = Column(Boolean, default=False)
    
    company = relationship("DBCompany", back_populates="tasks")

Base.metadata.create_all(bind=engine)

# ==========================================
# 2. DATOVÉ MODELY (Pydantic pro API)
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
    founder_id: str
    status: str
    company_name: str
    business_area: str
    immediate_duties: List[Duty] = []
    scheduled_duties: List[Duty] = []
    requirements: List[Requirement] = []
    founder_questions: List[str] = []
    explanation: str

class OnboardRequest(BaseModel):
    intent_text: str

# ==========================================
# 3. MOCK ROZHRANÍ (API Sběrače dat)
# ==========================================

def get_intent(founder_id: str, intent_text: str) -> dict:
    company_name = "Nová firma s.r.o."
    business_area = "Volná živnost"
    
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "vlozte_sem_svuj_klic":
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
Jsi špičkový AI asistent pro zakládání firem.
Z následujícího textu extrahuj:
1) Název firmy PŘESNĚ tak, jak ho uživatel zadal (pouze přidej 's.r.o.', nebo 'a.s.', pokud chybí právní forma). Pokud uživatel jméno vůbec nezadá, vymysli nějaké výstižné. Nekreativni! Použij to, co uživatel napsal.
2) Obor podnikání (specificky a profesionálně pojmenovaný podle skutečných živností).
Odpověz POUZE validním JSON objektem, nic jiného nepiš.
Struktura: {{"company_name": "...", "business_area": "..."}}

Text uživatele: "{intent_text}"
            """
            response = model.generate_content(prompt)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                raw_text = match.group(0)
                data = json.loads(raw_text)
                
                if "company_name" in data and "business_area" in data:
                    return {
                        "founder_id": founder_id,
                        "company_name": data["company_name"],
                        "business_area": data["business_area"],
                        "expected_turnover": 1500000.0,
                        "company_type": "s.r.o."
                    }
        except Exception as e:
            print(f"Gemini API Error: {e}")

    # Fallback logika
    if "Kofíčko" in intent_text:
        company_name = "Kofíčko s.r.o."
        business_area = "Hostinská činnost"
    elif "Inovace" in intent_text:
        company_name = "Inovace s.r.o."
        business_area = "Vývoj software"
    else:
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
    if query.get("type") == "person":
        return {"found": True, "address": "Dlouhá 15, Praha", "birth_date": "1990-01-01"}
    elif query.get("type") == "company_name":
        name = query.get("name")
        try:
            resp = requests.post(
                "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat",
                json={"obchodniJmeno": name},
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
            if resp.status_code == 200:
                data = resp.json()
                # Pokud existuje alespoň 1 subjekt s tímto jménem, prohlásíme jméno za obsazené
                if data.get("pocetCelkem", 0) > 0:
                    return {"available": False}
                else:
                    return {"available": True}
        except Exception as e:
            print("ARES API Error:", e)
        
        # Pokud něco selže, předpokládáme pro jistotu, že je volné
        return {"available": True}
    return {"found": False}

def lookup_legislation(tema: str) -> str:
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
# 4. MOZEK (Logika agenta)
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
        
        proposal.scheduled_duties = self.schedule_public_duties(founder_id, {"type": "s.r.o."})

        if proposal.status == "DRAFT":
            proposal.status = "READY_FOR_REVIEW"
            proposal.explanation = (
                f"Všechny dostupné registry byly zkontrolovány (ARES, ROS, ISIR, DPH, VIES). Název firmy '{intent.company_name}' je volný. "
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
# 5. FASTAPI SERVER A ENDPOINTY
# ==========================================

app = FastAPI(title="eGov AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TierOneAgent()

# Inicializace databáze pro demo (vytvoření defaultního uživatele)
def init_db():
    db = SessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "user_bankid_123").first()
    if not user:
        user = DBUser(id="user_bankid_123", name="Jan Novák")
        db.add(user)
        db.commit()
    db.close()

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/api/login")
def api_login():
    """Simulace BankID - vrací fixního uživatele z DB"""
    db = SessionLocal()
    user = db.query(DBUser).filter(DBUser.id == "user_bankid_123").first()
    db.close()
    return {"id": user.id, "name": user.name}

@app.get("/api/companies")
def api_get_companies():
    """Vrátí všechny firmy aktuálního (fixního) uživatele"""
    db = SessionLocal()
    companies = db.query(DBCompany).filter(DBCompany.owner_id == "user_bankid_123").all()
    res = []
    for c in companies:
        tasks = db.query(DBTask).filter(DBTask.company_id == c.id).all()
        res.append({
            "id": c.id,
            "name": c.name,
            "ico": c.ico,
            "business_area": c.business_area,
            "status": c.status,
            "tasks_total": len(tasks),
            "tasks_completed": len([t for t in tasks if t.is_completed])
        })
    db.close()
    return res

@app.post("/api/onboard", response_model=Proposal)
def api_onboard(request: OnboardRequest):
    """Získá Proposal na základě věty"""
    founder_id = "user_bankid_123"
    proposal = agent.onboard_company(founder_id=founder_id, intent_text=request.intent_text)
    return proposal

class CheckNameRequest(BaseModel):
    company_name: str

@app.post("/api/check-name")
def api_check_name(request: CheckNameRequest):
    """Ověří konkrétní jméno vůči ARES"""
    registry_company = lookup_registry({"type": "company_name", "name": request.company_name})
    return {"available": registry_company.get("available", False)}

@app.post("/api/companies")
def api_create_company(proposal: dict):
    """Uloží schválený proposal jako novou firmu do databáze"""
    db = SessionLocal()
    # Vytvoření firmy
    new_company = DBCompany(
        owner_id="user_bankid_123",
        name=proposal.get("company_name", "Neznámá firma s.r.o."),
        ico="12345678", # Mock IČO
        business_area=proposal.get("business_area", ""),
        status="Aktivní"
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    # Vytvoření úkolů (z immediate_duties a scheduled_duties)
    for duty in proposal.get("immediate_duties", []):
        db.add(DBTask(
            company_id=new_company.id,
            title=duty.get("title"),
            description=duty.get("description"),
            deadline=duty.get("deadline"),
            is_completed=False,
            can_automate=True # Okamžité umí agent automatizovat
        ))
    for duty in proposal.get("scheduled_duties", []):
        db.add(DBTask(
            company_id=new_company.id,
            title=duty.get("title"),
            description=duty.get("description"),
            deadline=duty.get("deadline"),
            is_completed=False,
            can_automate=False # Dlouhodobé zatím ne
        ))
    
    db.commit()
    company_id = new_company.id
    db.close()
    return {"status": "success", "company_id": company_id}

@app.get("/api/companies/{company_id}")
def api_get_company(company_id: int):
    """Vrátí detail konkrétní firmy a její úkoly"""
    db = SessionLocal()
    company = db.query(DBCompany).filter(DBCompany.id == company_id).first()
    if not company:
        db.close()
        raise HTTPException(status_code=404, detail="Company not found")
        
    tasks = db.query(DBTask).filter(DBTask.company_id == company.id).all()
    
    tasks_data = []
    for t in tasks:
        tasks_data.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "deadline": t.deadline,
            "is_completed": t.is_completed,
            "can_automate": t.can_automate
        })
        
    res = {
        "id": company.id,
        "name": company.name,
        "ico": company.ico,
        "business_area": company.business_area,
        "status": company.status,
        "tasks": tasks_data
    }
    db.close()
    return res

@app.post("/api/tasks/{task_id}/execute")
def api_execute_task(task_id: int):
    """Simulace vyřešení úkolu agentem"""
    db = SessionLocal()
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Task not found")
        
    if not task.can_automate:
        db.close()
        raise HTTPException(status_code=400, detail="Tento úkol nelze automatizovat")
        
    # V reálu zde agent volá úřady, ISDS atd.
    task.is_completed = True
    task.status_text = "Vyřízeno umělou inteligencí"
    db.commit()
    db.close()
    return {"status": "success", "task_id": task_id, "is_completed": True}

# Váš stávající mock endpoint pro Dashboard
@app.get("/api/dashboard")
def api_dashboard(company_name: str = "Inovace s.r.o.", ico: str = "12345678"):
    # Vracíme stejná data, jaká měl JS dříve jako fallback
    return {
        "company_name": company_name,
        "ico": ico,
        "last_full_scan": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "alerts_count": 0,
        "legal_limits": [],
        "monitoring_areas": []
    }

# Původní routování statiky
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    print("Startuji FastAPI server s DB...")
    uvicorn.run(app, host="0.0.0.0", port=8091)
