import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

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

# ==========================================
# 2. MOCK ROZHRANÍ (API Sběrače dat)
# ==========================================

def get_intent(founder_id: str) -> dict:
    """Vrátí počáteční záměr zakladatele."""
    # V reálu by toto volalo např. databázi s odpověďmi z úvodního formuláře
    return {
        "founder_id": founder_id,
        "company_name": "Inovace s.r.o.",
        "business_area": "Vývoj software",
        "expected_turnover": 1500000.0,
        "company_type": "s.r.o."
    }

def lookup_registry(query: dict) -> dict:
    """Sáhne do registrů (ARES, Živnostenský rejstřík, ROS) pro údaje."""
    # Mock odpověď - simulace hledání
    if query.get("type") == "person":
        # Pokud neznáme rodné číslo, předstíráme, že ho registry nemají
        # Zde pro demo vracíme jakože úspěch, pokud zadáme jméno z našeho dema
        return {"found": True, "address": "Dlouhá 15, Praha", "birth_date": "1990-01-01"}
    elif query.get("type") == "company_name":
        # Ověření volnosti jména
        name = query.get("name")
        if name == "Inovace s.r.o.":
            return {"available": True}
        return {"available": False}
    return {"found": False}

def lookup_legislation(tema: str) -> str:
    """Získá relevantní pravidla pro daný obor z platné legislativy."""
    # V reálu volání LLM / RAG (Retrieval-Augmented Generation) nad zákony
    if "software" in tema.lower():
        return "Obor: Vývoj software. Typ živnosti: Volná. Nejsou vyžadovány žádné speciální koncese ani prokazování praxe."
    elif "restaurace" or "hostinská" in tema.lower():
        return "Obor: Hostinská činnost. Typ živnosti: Řemeslná. Vyžaduje prokázání odborné způsobilosti (vyučení v oboru nebo praxe)."
    return "Živnost volná, bez speciálních požadavků."

def schedule(founder_id: str, povinnost: str, termin: str) -> bool:
    """Naplánuje budoucí úkol/hlídání do uživatelského kalendáře."""
    print(f"[KALENDÁŘ] Naplánováno pro {founder_id}: {povinnost} na termín {termin}")
    return True

def ask_founder(founder_id: str, otazka: str) -> str:
    """Záchranná brzda - dotaz na uživatele POUZE při nedostatku dat z registrů."""
    # V reálu by toto vytvořilo notifikaci pro uživatele (např. e-mail nebo alert v aplikaci)
    # a asynchronně čekalo na odpověď. Žádné halucinace.
    print(f"[DOTAZ NA ZAKLADATELE {founder_id}]: {otazka}")
    return "User response placeholder"

# ==========================================
# 3. MOZEK (Logika agenta)
# ==========================================

class TierOneAgent:
    """
    Tier 1 Agent pro chytrou asistenci při zakládání a hlídání firmy.
    Pracuje výhradně s veřejnými registry a legislativou. Nevymýšlí si (nehalucinuje).
    Výstupem je datová struktura Proposal, nikoli přímá akce bez vědomí uživatele.
    """
    def __init__(self):
        pass
        
    def onboard_company(self, founder_id: str) -> Proposal:
        """
        Fáze 1: Chytrý Onboarding. 
        Založení firmy metodou once-only (data sháníme, neptáme se uživatele na zřejmosti).
        """
        # 1. Získání záměru od uživatele
        intent_data = get_intent(founder_id)
        intent = Intent(**intent_data)
        
        proposal = Proposal(
            founder_id=founder_id,
            status="DRAFT",
            company_name=intent.company_name,
            business_area=intent.business_area,
            explanation=""
        )

        # 2. Kontrola v registrech (Osobní údaje a volnost jména)
        registry_person = lookup_registry({"type": "person", "name": "Jan Novák"}) # Mock hledání osoby
        if not registry_person.get("found"):
            # Princip: Žádné halucinace. Nemáme-li data v registru, ptáme se uživatele.
            question = "Nenašli jsme vaše kompletní údaje v registru obyvatel. Prosím, doplňte své trvalé bydliště a datum narození."
            ask_founder(founder_id, question)
            proposal.status = "MISSING_DATA"
            proposal.founder_questions.append(question)
            proposal.explanation = "Pro pokračování potřebujeme doplnit chybějící osobní údaje, které nebyly nalezeny v registrech."
            return proposal

        registry_company = lookup_registry({"type": "company_name", "name": intent.company_name})
        if not registry_company.get("available"):
            # Pokud je jméno nedostupné, nepokračujeme slepě, ale vyžádáme interakci.
            question = f"Název firmy '{intent.company_name}' je již obsazen nebo v ARES figuruje podobný subjekt. Jaký jiný název chcete použít?"
            ask_founder(founder_id, question)
            proposal.status = "MISSING_DATA"
            proposal.founder_questions.append(question)
            proposal.explanation = "Název firmy koliduje s existujícím subjektem. Navrhněte prosím jiný název."
            return proposal

        # 3. Analýza legislativy a požadavků na základě předmětu podnikání
        leg_info = lookup_legislation(intent.business_area)
        
        # Elementární vyhodnocení textu z legislativy (v praxi by vracela strukturovaná data)
        if "Řemeslná" in leg_info or "Koncesovaná" in leg_info:
            proposal.requirements.append(
                Requirement(
                    title="Doložení odborné způsobilosti", 
                    description=f"Pro obor '{intent.business_area}' legislativa vyžaduje doložení praxe nebo vzdělání. Důvod: {leg_info}"
                )
            )

        # 4. Příprava okamžitých povinností hned po založení (Tier 1 dohled)
        proposal.immediate_duties.extend([
            Duty(
                title="Registrace k dani z příjmů (DPPO)",
                description="Povinná registrace u místně příslušného finančního úřadu do 15 dnů od vzniku.",
                deadline=(datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"),
                is_immediate=True
            ),
            Duty(
                title="Zápis do evidence skutečných majitelů (ESM)",
                description="Návrh na zápis musí být podán bez zbytečného odkladu.",
                deadline=(datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d"), # obvykle do 15 dnů
                is_immediate=True
            ),
            Duty(
                title="Označení sídla štítkem",
                description="Viditelné označení sídla firmy názvem a IČO.",
                deadline=(datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
                is_immediate=True
            )
        ])

        proposal.status = "READY_FOR_REVIEW"
        proposal.explanation = (
            f"Všechny dostupné registry byly zkontrolovány. Název firmy '{intent.company_name}' je volný. "
            f"Připravil jsem návrh na založení a seznam povinných podkladů i okamžitých povinností po zápisu do OR."
        )

        return proposal

    def schedule_public_duties(self, founder_id: str, company_data: dict) -> List[Duty]:
        """
        Fáze 2: Hlídání v čase. Naplánování dlouhodobých povinností zjištěných z legislativy.
        """
        scheduled = []
        
        # Tyto údaje by agent v reálu zjišťoval dynamickou analýzou legislativy 
        # pro daný typ firmy (např. s.r.o. vs OSVČ) a její stav.
        # Pro mock účely vracíme běžné povinnosti pro s.r.o.
        
        # 1. Daňové přiznání DPPO
        # Běžně do 4 měsíců po konci účetního období (při elektronickém podání)
        current_year = datetime.now().year
        dppo_duty = Duty(
            title="Podání daňového přiznání (DPPO)",
            description="Elektronické podání přiznání k dani z příjmů právnických osob za minulý rok.",
            deadline=f"{current_year + 1}-05-02"
        )
        scheduled.append(dppo_duty)
        
        # 2. Účetní závěrka
        zav_duty = Duty(
            title="Založení účetní závěrky do sbírky listin",
            description="Zveřejnění schválené účetní závěrky v obchodním rejstříku.",
            deadline=f"{current_year + 1}-07-31" 
        )
        scheduled.append(zav_duty)
        
        # Fyzické zapsání do kalendáře uživatele přes poskytnuté API rozhraní
        for duty in scheduled:
            schedule(founder_id, duty.title, duty.deadline)
            
        return scheduled

if __name__ == "__main__":
    # --- JEDNODUCHÉ DEMO PRO ŽIVOU UKÁZKU ---
    print("Spouštím Tier 1 Agenta...\n")
    agent = TierOneAgent()
    
    print("="*40)
    print("FÁZE 1: CHYTRÝ ONBOARDING")
    print("="*40)
    proposal = agent.onboard_company(founder_id="user_123")
    print("\n[VÝSTUP AGENTA - PROPOSAL]:")
    print(proposal.model_dump_json(indent=2))
    
    print("\n" + "="*40)
    print("FÁZE 2: HLÍDÁNÍ V ČASE (SCHEDULING)")
    print("="*40)
    if proposal.status == "READY_FOR_REVIEW":
        tasks = agent.schedule_public_duties(founder_id="user_123", company_data={"type": "s.r.o."})
        print(f"\nNaplánováno {len(tasks)} dlouhodobých povinností do kalendáře.")
