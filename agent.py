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

# --- NOVÉ MODELY PRO DASHBOARD ---

class MonitoringArea(BaseModel):
    """Oblast, kterou agent průběžně sleduje."""
    id: str
    title: str
    description: str
    registry_name: str
    registry_url: str
    api_url: str
    icon: str  # FontAwesome class
    status: str = Field(description="'ok', 'warning', 'error', 'info'")
    status_text: str
    last_checked: str
    details: List[str] = []

class LegalLimit(BaseModel):
    """Zákonný limit, který agent hlídá."""
    id: str
    title: str
    law_reference: str
    paragraph: str
    current_value: float
    limit_value: float
    unit: str
    status: str = Field(description="'ok', 'warning', 'danger'")
    status_text: str
    icon: str
    details: str

class DashboardData(BaseModel):
    """Kompletní výstup dashboardu."""
    company_name: str
    ico: str
    monitoring_areas: List[MonitoringArea] = []
    legal_limits: List[LegalLimit] = []
    last_full_scan: str
    alerts_count: int = 0

# ==========================================
# 2. MOCK ROZHRANÍ (API Sběrače dat)
# ==========================================

def get_intent(founder_id: str, intent_text: str) -> dict:
    """Vrátí počáteční záměr zakladatele na základě zadání z frontendu."""
    company_name = "Nová firma s.r.o."
    business_area = "Volná živnost"
    
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
    """Sáhne do registrů (ARES, Živnostenský rejstřík, ROS) pro údaje."""
    if query.get("type") == "person":
        return {"found": True, "address": "Dlouhá 15, Praha", "birth_date": "1990-01-01"}
    elif query.get("type") == "company_name":
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
# 2b. MOCK FUNKCE PRO 7 REGISTRŮ
# ==========================================

def check_ares(ico: str) -> MonitoringArea:
    """ARES – Administrativní registr ekonomických subjektů. Ověření IČO, sídla, jednatelů."""
    return MonitoringArea(
        id="ares",
        title="Platnost údajů a zápisů",
        description="Kontrola IČO, sídla firmy, statutárních orgánů a předmětů podnikání v ARES.",
        registry_name="ARES (Administrativní registr ekonomických subjektů)",
        registry_url="https://mf.gov.cz/cs/ministerstvo/informacni-systemy/ares",
        api_url="https://ares.gov.cz/ekonomicke-subjekty-v-be/rest",
        icon="fa-solid fa-building-columns",
        status="ok",
        status_text="Všechny údaje v ARES jsou aktuální",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "IČO: 12345678 – platné",
            "Sídlo: Dlouhá 15, 110 00 Praha 1 – odpovídá",
            "Jednatel: Jan Novák – zapsán",
            "Předmět podnikání: aktivní"
        ]
    )

def check_dph_registry(ico: str) -> MonitoringArea:
    """Registr DPH – Portál MOJE daně. Spolehlivost plátce a ověření bankovních účtů."""
    return MonitoringArea(
        id="dph_registry",
        title="Spolehlivost plátce DPH",
        description="Ověření spolehlivosti plátce DPH a registrovaných bankovních účtů pro zveřejnění.",
        registry_name="Registr DPH (Portál MOJE daně)",
        registry_url="https://financnisprava.gov.cz/registr-dph",
        api_url="https://adisrws.mfcr.cz/adistc/axis2/services/RWSService",
        icon="fa-solid fa-file-invoice-dollar",
        status="ok",
        status_text="Plátce je spolehlivý, bankovní účet zveřejněn",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Stav plátce: spolehlivý",
            "Registrace k DPH: platná",
            "Zveřejněný účet: CZ65 0800 0000 1923 4567 8901",
            "Nespolehlivost: NE"
        ]
    )

def check_isds() -> MonitoringArea:
    """ISDS – Informační systém datových schránek. Stahování zpráv a hlídání doručení."""
    return MonitoringArea(
        id="isds",
        title="Datové schránky",
        description="Sledování nových zpráv v datové schránce, hlídání lhůt doručení a fikce doručení.",
        registry_name="ISDS (Informační systém datových schránek)",
        registry_url="https://mojedatovaschranka.cz",
        api_url="https://info.mojedatovaschranka.cz",
        icon="fa-solid fa-envelope-open-text",
        status="warning",
        status_text="2 nepřečtené zprávy – lhůta doručení vyprší za 3 dny",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Celkem zpráv: 47",
            "Nepřečtené: 2",
            "Nejstarší nepřečtená: od FÚ Praha 1 (před 7 dny)",
            "⚠ Fikce doručení nastane: " + (datetime.now() + timedelta(days=3)).strftime("%d.%m.%Y")
        ]
    )

def check_isir(ico: str) -> MonitoringArea:
    """ISIR – Insolvenční rejstřík. Prověřování partnerů a sledování vlastní insolvence."""
    return MonitoringArea(
        id="isir",
        title="Insolvence a úpadek firem",
        description="Prověřování obchodních partnerů v insolvenčním rejstříku a monitoring vlastní firmy.",
        registry_name="Insolvenční rejstřík (ISIR)",
        registry_url="https://isir.justice.cz",
        api_url="https://data.gov.cz",
        icon="fa-solid fa-triangle-exclamation",
        status="ok",
        status_text="Žádné insolvenční řízení nenalezeno",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Vlastní firma: bez nálezu",
            "Sledovaní partneři: 5",
            "Partner s nálezem: 0",
            "Poslední kontrola partnerů: dnes"
        ]
    )

def check_e_sbirka() -> MonitoringArea:
    """e-Sbírka – Sbírka zákonů a mezinárodních smluv. Sledování legislativních změn."""
    return MonitoringArea(
        id="e_sbirka",
        title="Legislativní změny na míru",
        description="Automatické sledování nových zákonů a novel relevantních pro obor podnikání.",
        registry_name="Sbírka zákonů a mezinárodních smluv (e-Sbírka)",
        registry_url="https://e-sbirka.cz",
        api_url="https://opendata.e-sbirka.cz",
        icon="fa-solid fa-scale-balanced",
        status="info",
        status_text="Novela zákona o DPH účinná od 1.1. příštího roku",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Sledovaných předpisů: 12",
            f"Nové: Novela zák. 235/2004 Sb. (účinnost 1.1.{datetime.now().year + 1})",
            "Zákoník práce: beze změn",
            "Živnostenský zákon: beze změn"
        ]
    )

def check_vies(vat_id: str) -> MonitoringArea:
    """VIES – VAT Information Exchange System. Ověření zahraničních DPH v EU."""
    return MonitoringArea(
        id="vies",
        title="Zahraniční DPH a subjekty v EU",
        description="Ověřování DIČ zahraničních partnerů v systému VIES Evropské komise.",
        registry_name="VIES (VAT Information Exchange System)",
        registry_url="https://ec.europa.eu/taxation_customs/vies",
        api_url="https://ec.europa.eu/taxation_customs/vies/rest-api",
        icon="fa-solid fa-earth-europe",
        status="ok",
        status_text="Všichni EU partneři mají platné DIČ",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Sledovaných EU partnerů: 3",
            "DE123456789 – platné (Německo)",
            "SK2020123456 – platné (Slovensko)",
            "AT U12345678 – platné (Rakousko)"
        ]
    )

def check_partner_insolvency() -> MonitoringArea:
    """Doplňkové prověřování obchodních partnerů – křížová kontrola ISIR + ARES."""
    return MonitoringArea(
        id="partner_check",
        title="Prověřování partnerů",
        description="Kontinuální monitoring bonity a insolvence klíčových obchodních partnerů.",
        registry_name="ISIR + ARES (křížová kontrola)",
        registry_url="https://isir.justice.cz",
        api_url="https://ares.gov.cz/ekonomicke-subjekty-v-be/rest",
        icon="fa-solid fa-user-shield",
        status="warning",
        status_text="1 partner vykazuje zhoršenou bonitu",
        last_checked=datetime.now().strftime("%d.%m.%Y %H:%M"),
        details=[
            "Sledovaných partnerů: 5",
            "⚠ ABC Trading s.r.o. – pokles bonity (zpoždění plateb)",
            "XYZ Tech a.s. – bez nálezu",
            "DEF Logistika s.r.o. – bez nálezu"
        ]
    )

# ==========================================
# 2c. MOCK FUNKCE PRO 3 ZÁKONNÉ LIMITY
# ==========================================

def check_vat_limit(current_turnover: float) -> LegalLimit:
    """Hlídání limitu 2 000 000 Kč pro povinnou registraci k DPH (§6 zák. 235/2004 Sb.)."""
    limit = 2000000.0
    pct = (current_turnover / limit) * 100
    if pct >= 95:
        status = "danger"
        status_text = f"KRITICKÉ: Obrat {current_turnover:,.0f} Kč dosahuje {pct:.0f}% limitu!"
    elif pct >= 75:
        status = "warning"
        status_text = f"Pozor: Obrat {current_turnover:,.0f} Kč je na {pct:.0f}% limitu."
    else:
        status = "ok"
        status_text = f"Obrat {current_turnover:,.0f} Kč – bez rizika ({pct:.0f}% limitu)."
    
    return LegalLimit(
        id="vat_limit",
        title="Hlídání limitu 2 000 000 Kč pro DPH",
        law_reference="Zákon č. 235/2004 Sb., o dani z přidané hodnoty",
        paragraph="§ 6 (Osoby povinné k dani)",
        current_value=current_turnover,
        limit_value=limit,
        unit="Kč",
        status=status,
        status_text=status_text,
        icon="fa-solid fa-coins",
        details=f"Obrat za posledních 12 měsíců: {current_turnover:,.0f} Kč z limitu {limit:,.0f} Kč. Při překročení vzniká povinnost registrace k DPH."
    )

def check_identified_person(has_eu_ads: bool, eu_spend: float) -> LegalLimit:
    """Identifikovaná osoba – přijetí služby z jiného členského státu EU (§6h zák. 235/2004 Sb.)."""
    limit_value = 1.0  # binární – buď je relevantní nebo ne
    current = 1.0 if has_eu_ads else 0.0
    
    if has_eu_ads and eu_spend > 0:
        status = "warning"
        status_text = f"Detekována fakturace z EU (Google/FB Ads): {eu_spend:,.0f} Kč – povinnost stát se identifikovanou osobou!"
    else:
        status = "ok"
        status_text = "Žádné přijaté služby z EU – povinnost nevzniká."
    
    return LegalLimit(
        id="identified_person",
        title="Identifikovaná osoba (EU reklamy)",
        law_reference="Zákon č. 235/2004 Sb., o dani z přidané hodnoty",
        paragraph="§ 6h (Přijetí služby z jiného členského státu)",
        current_value=eu_spend,
        limit_value=100000.0,  # zobrazovací limit pro progress bar
        unit="Kč",
        status=status,
        status_text=status_text,
        icon="fa-solid fa-ad",
        details=f"Služby z EU (Google Ads, Facebook Ads apod.): {eu_spend:,.0f} Kč. Při přijetí jakékoliv služby z EU se neplátce DPH musí registrovat jako identifikovaná osoba."
    )

def check_dpp_limit(hours_worked: float) -> LegalLimit:
    """Limity pro brigádníky – DPP do 300 hodin za rok (§75 zák. 262/2006 Sb.)."""
    limit = 300.0
    pct = (hours_worked / limit) * 100
    if pct >= 90:
        status = "danger"
        status_text = f"KRITICKÉ: Odpracováno {hours_worked:.0f}h z {limit:.0f}h – zbývá jen {limit - hours_worked:.0f}h!"
    elif pct >= 70:
        status = "warning"
        status_text = f"Pozor: Odpracováno {hours_worked:.0f}h z {limit:.0f}h ({pct:.0f}%)."
    else:
        status = "ok"
        status_text = f"Odpracováno {hours_worked:.0f}h z {limit:.0f}h – bez rizika ({pct:.0f}%)."
    
    return LegalLimit(
        id="dpp_limit",
        title="Limity pro brigádníky (DPP)",
        law_reference="Zákon č. 262/2006 Sb., zákoník práce",
        paragraph="§ 75 (Dohoda o provedení práce)",
        current_value=hours_worked,
        limit_value=limit,
        unit="hodin/rok",
        status=status,
        status_text=status_text,
        icon="fa-solid fa-clock",
        details=f"Celkem odpracováno na DPP: {hours_worked:.0f} hodin z ročního limitu {limit:.0f} hodin u jednoho zaměstnavatele."
    )

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

    def get_dashboard(self, ico: str = "12345678", company_name: str = "Inovace s.r.o.") -> DashboardData:
        """Sestaví kompletní dashboard se všemi sledovanými oblastmi a limity."""
        
        # 7 oblastí sledování
        monitoring = [
            check_ares(ico),
            check_dph_registry(ico),
            check_isds(),
            check_isir(ico),
            check_e_sbirka(),
            check_vies(f"CZ{ico}"),
            check_partner_insolvency(),
        ]
        
        # 3 zákonné limity (mock data)
        limits = [
            check_vat_limit(current_turnover=1650000.0),       # 82.5% limitu
            check_identified_person(has_eu_ads=True, eu_spend=45000.0),
            check_dpp_limit(hours_worked=210.0),               # 70% limitu
        ]
        
        # Počet alertů
        alerts = sum(1 for m in monitoring if m.status in ("warning", "error"))
        alerts += sum(1 for l in limits if l.status in ("warning", "danger"))
        
        return DashboardData(
            company_name=company_name,
            ico=ico,
            monitoring_areas=monitoring,
            legal_limits=limits,
            last_full_scan=datetime.now().strftime("%d.%m.%Y %H:%M"),
            alerts_count=alerts
        )

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

@app.get("/api/dashboard", response_model=DashboardData)
def api_dashboard(company_name: str = "Inovace s.r.o.", ico: str = "12345678"):
    """
    Vrátí kompletní dashboard se stavem všech 7 monitorovaných registrů
    a 3 zákonných limitů.
    """
    return agent.get_dashboard(ico=ico, company_name=company_name)

# Servírování statických souborů (Frontend)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    print("Startuji FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
