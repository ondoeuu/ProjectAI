document.addEventListener('DOMContentLoaded', () => {
    
    // --- UI Elements ---
    const stepIdentity = document.getElementById('step-identity');
    const stepIntent = document.getElementById('step-intent');
    const stepProcessing = document.getElementById('step-processing');
    const stepProposal = document.getElementById('step-proposal');
    const stepDashboard = document.getElementById('step-dashboard');

    const btnLogin = document.getElementById('btn-login');
    const inputIntent = document.getElementById('input-intent');
    const btnSubmitIntent = document.getElementById('btn-submit-intent');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnCancel = document.getElementById('btn-cancel');
    const headerNav = document.getElementById('header-nav');

    // Globální data pro sdílení mezi kroky
    let currentProposal = null;
    let currentDashboard = null;

    // --- Navigation Logic ---
    function showStep(stepElement) {
        document.querySelectorAll('.step').forEach(el => {
            el.classList.remove('active');
            el.classList.add('hidden');
        });
        stepElement.classList.remove('hidden');
        setTimeout(() => stepElement.classList.add('active'), 10);
    }

    // 1. Login (Mock BankID) -> Intent
    btnLogin.addEventListener('click', () => {
        btnLogin.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Přihlašuji...';
        setTimeout(() => {
            showStep(stepIntent);
            inputIntent.focus();
        }, 1000);
    });

    // 2. Intent -> Processing -> API Call -> Proposal
    async function processIntent() {
        const intentVal = inputIntent.value.trim();
        if(!intentVal) return;

        showStep(stepProcessing);
        runAIProcessing();
        
        try {
            const response = await fetch('/api/onboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ intent_text: intentVal })
            });
            
            if (!response.ok) throw new Error("Server error");
            
            currentProposal = await response.json();
        } catch (error) {
            console.error("Chyba při komunikaci s API:", error);
            // Fallback na mock data
            currentProposal = {
                founder_id: "user_bankid_123",
                status: "READY_FOR_REVIEW",
                company_name: "Inovace s.r.o.",
                business_area: "Vývoj software",
                immediate_duties: [
                    { title: "Registrace k dani z příjmů (DPPO)", description: "Povinná registrace u finančního úřadu do 15 dnů.", deadline: "Do 15 dnů od vzniku" },
                    { title: "Zápis do evidence skutečných majitelů", description: "Návrh na zápis musí být podán bez zbytečného odkladu.", deadline: "Bez zbytečného odkladu" }
                ],
                scheduled_duties: [
                    { title: "Podání daňového přiznání (DPPO)", deadline: "2. května příští rok" },
                    { title: "Založení účetní závěrky do sbírky listin", deadline: "31. července příští rok" }
                ],
                requirements: [
                    { title: "Ohlášení volné živnosti", description: "Pro obor Vývoj software není vyžadována koncese. Postačuje ohlášení." }
                ],
                explanation: "Všechny dostupné registry byly zkontrolovány (ARES, ROS, ISIR, DPH, VIES). Název firmy 'Inovace s.r.o.' je volný."
            };
        }
    }

    btnSubmitIntent.addEventListener('click', processIntent);
    inputIntent.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') processIntent();
    });

    // 3. AI Processing Animation (6 kroků pro 6 registrů)
    function runAIProcessing() {
        const steps = document.querySelectorAll('.proc-step');
        let currentStep = 0;

        const interval = setInterval(() => {
            if (currentStep > 0) {
                const prev = steps[currentStep - 1];
                prev.classList.remove('active-step');
                prev.classList.add('done-step');
                prev.innerHTML = prev.innerHTML.replace('fa-circle-notch fa-spin', 'fa-check-circle');
            }

            if (currentStep < steps.length) {
                const curr = steps[currentStep];
                curr.classList.remove('pending');
                curr.classList.add('active-step');
                currentStep++;
            } else {
                clearInterval(interval);
                setTimeout(() => {
                    if (currentProposal) {
                        populateProposal(currentProposal);
                    }
                    showStep(stepProposal);
                }, 600);
            }
        }, 1200);
    }

    // 4. Naplnění Proposal UI
    function populateProposal(data) {
        document.getElementById('prop-explanation').innerText = data.explanation;
        document.getElementById('prop-company-name').innerText = data.company_name;
        document.getElementById('prop-business-area').innerText = data.business_area;

        const reqContainer = document.getElementById('prop-requirements');
        reqContainer.innerHTML = '';
        data.requirements.forEach(req => {
            reqContainer.innerHTML += `
                <li class="req-item">
                    <h4>${req.title}</h4>
                    <p>${req.description}</p>
                </li>
            `;
        });

        const dutiesContainer = document.getElementById('prop-duties');
        dutiesContainer.innerHTML = '';
        data.immediate_duties.forEach(duty => {
            dutiesContainer.innerHTML += `
                <div class="duty-card">
                    <h4>${duty.title}</h4>
                    <p>${duty.description}</p>
                    <span class="deadline"><i class="fa-regular fa-clock"></i> ${duty.deadline}</span>
                </div>
            `;
        });
    }

    // 5. Potvrzení -> Načtení Dashboardu
    btnConfirm.addEventListener('click', async () => {
        btnConfirm.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Zakládám firmu a aktivuji monitoring...';
        
        const companyName = currentProposal ? currentProposal.company_name : 'Inovace s.r.o.';
        
        try {
            const response = await fetch(`/api/dashboard?company_name=${encodeURIComponent(companyName)}&ico=12345678`);
            if (!response.ok) throw new Error("Dashboard API error");
            currentDashboard = await response.json();
        } catch (error) {
            console.error("Chyba při načítání dashboardu:", error);
            currentDashboard = getFallbackDashboard(companyName);
        }
        
        setTimeout(() => {
            populateDashboard(currentDashboard);
            headerNav.style.display = 'flex';
            showStep(stepDashboard);
        }, 1500);
    });

    btnCancel.addEventListener('click', () => {
        location.reload();
    });

    // ==========================================
    // DASHBOARD LOGIC
    // ==========================================

    function populateDashboard(data) {
        // Hero
        document.getElementById('dash-company-name').innerText = data.company_name;
        document.getElementById('dash-ico').innerText = data.ico;
        document.getElementById('dash-last-scan').innerText = data.last_full_scan;
        
        const alertsCount = data.alerts_count;
        const alertsEl = document.getElementById('dash-alerts-count');
        alertsEl.innerText = alertsCount;
        const alertsPill = document.getElementById('dash-alerts-pill');
        if (alertsCount > 0) {
            alertsPill.classList.add('has-alerts');
        }

        // Zákonné limity
        const limitsContainer = document.getElementById('dash-limits');
        limitsContainer.innerHTML = '';
        data.legal_limits.forEach((limit, idx) => {
            const percentage = Math.min((limit.current_value / limit.limit_value) * 100, 100);
            const statusClass = limit.status; // ok, warning, danger
            
            limitsContainer.innerHTML += `
                <div class="limit-card glass-card slide-up" style="animation-delay: ${idx * 0.1}s">
                    <div class="limit-header">
                        <div class="limit-icon ${statusClass}">
                            <i class="${limit.icon}"></i>
                        </div>
                        <div class="limit-badge ${statusClass}">${getStatusLabel(limit.status)}</div>
                    </div>
                    <h3 class="limit-title">${limit.title}</h3>
                    <p class="limit-law"><i class="fa-solid fa-paragraph"></i> ${limit.paragraph}</p>
                    <p class="limit-law-ref">${limit.law_reference}</p>
                    
                    <div class="progress-wrapper">
                        <div class="progress-bar">
                            <div class="progress-fill ${statusClass}" style="width: 0%" data-target="${percentage}"></div>
                        </div>
                        <div class="progress-labels">
                            <span>${formatNumber(limit.current_value)} ${limit.unit}</span>
                            <span>${formatNumber(limit.limit_value)} ${limit.unit}</span>
                        </div>
                    </div>
                    
                    <p class="limit-status-text">${limit.status_text}</p>
                    <p class="limit-details">${limit.details}</p>
                </div>
            `;
        });

        // Monitoring registrů
        const monitoringContainer = document.getElementById('dash-monitoring');
        monitoringContainer.innerHTML = '';
        data.monitoring_areas.forEach((area, idx) => {
            const statusClass = area.status;
            const detailsHtml = area.details.map(d => `<li>${d}</li>`).join('');
            
            monitoringContainer.innerHTML += `
                <div class="monitor-card glass-card slide-up" style="animation-delay: ${idx * 0.08}s">
                    <div class="monitor-header">
                        <div class="monitor-icon ${statusClass}">
                            <i class="${area.icon}"></i>
                        </div>
                        <div class="monitor-status-dot ${statusClass}" title="${getStatusLabel(area.status)}"></div>
                    </div>
                    <h3 class="monitor-title">${area.title}</h3>
                    <p class="monitor-registry">${area.registry_name}</p>
                    <p class="monitor-description">${area.description}</p>
                    
                    <div class="monitor-status-bar ${statusClass}">
                        <i class="fa-solid ${getStatusIcon(area.status)}"></i>
                        <span>${area.status_text}</span>
                    </div>
                    
                    <ul class="monitor-details">
                        ${detailsHtml}
                    </ul>
                    
                    <div class="monitor-footer">
                        <span class="monitor-time"><i class="fa-regular fa-clock"></i> ${area.last_checked}</span>
                        <a href="${area.registry_url}" target="_blank" class="monitor-link" title="Otevřít registr">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        </a>
                    </div>
                </div>
            `;
        });

        // Animace progress barů po renderování
        setTimeout(() => animateProgressBars(), 300);
    }

    function animateProgressBars() {
        document.querySelectorAll('.progress-fill').forEach(bar => {
            const target = bar.getAttribute('data-target');
            setTimeout(() => {
                bar.style.width = target + '%';
            }, 100);
        });
    }

    function getStatusLabel(status) {
        const labels = {
            'ok': 'V pořádku',
            'warning': 'Upozornění',
            'danger': 'Kritické',
            'error': 'Chyba',
            'info': 'Informace'
        };
        return labels[status] || status;
    }

    function getStatusIcon(status) {
        const icons = {
            'ok': 'fa-circle-check',
            'warning': 'fa-exclamation-triangle',
            'danger': 'fa-circle-xmark',
            'error': 'fa-circle-xmark',
            'info': 'fa-circle-info'
        };
        return icons[status] || 'fa-circle-info';
    }

    function formatNumber(num) {
        if (num >= 1000) {
            return num.toLocaleString('cs-CZ');
        }
        return num.toString();
    }

    // Fallback dashboard data pokud API není dostupné
    function getFallbackDashboard(companyName) {
        return {
            company_name: companyName,
            ico: "12345678",
            last_full_scan: new Date().toLocaleString('cs-CZ'),
            alerts_count: 3,
            legal_limits: [
                {
                    id: "vat_limit", title: "Hlídání limitu 2 000 000 Kč pro DPH",
                    law_reference: "Zákon č. 235/2004 Sb., o dani z přidané hodnoty",
                    paragraph: "§ 6 (Osoby povinné k dani)",
                    current_value: 1650000, limit_value: 2000000, unit: "Kč",
                    status: "warning", status_text: "Pozor: Obrat 1 650 000 Kč je na 82% limitu.",
                    icon: "fa-solid fa-coins",
                    details: "Obrat za posledních 12 měsíců: 1 650 000 Kč z limitu 2 000 000 Kč."
                },
                {
                    id: "identified_person", title: "Identifikovaná osoba (EU reklamy)",
                    law_reference: "Zákon č. 235/2004 Sb., o dani z přidané hodnoty",
                    paragraph: "§ 6h (Přijetí služby z jiného členského státu)",
                    current_value: 45000, limit_value: 100000, unit: "Kč",
                    status: "warning", status_text: "Detekována fakturace z EU (Google/FB Ads): 45 000 Kč",
                    icon: "fa-solid fa-ad",
                    details: "Služby z EU (Google Ads, Facebook Ads apod.): 45 000 Kč."
                },
                {
                    id: "dpp_limit", title: "Limity pro brigádníky (DPP)",
                    law_reference: "Zákon č. 262/2006 Sb., zákoník práce",
                    paragraph: "§ 75 (Dohoda o provedení práce)",
                    current_value: 210, limit_value: 300, unit: "hodin/rok",
                    status: "warning", status_text: "Pozor: Odpracováno 210h z 300h (70%).",
                    icon: "fa-solid fa-clock",
                    details: "Celkem odpracováno na DPP: 210 hodin z ročního limitu 300 hodin."
                }
            ],
            monitoring_areas: [
                {
                    id: "ares", title: "Platnost údajů a zápisů",
                    description: "Kontrola IČO, sídla firmy, statutárních orgánů a předmětů podnikání v ARES.",
                    registry_name: "ARES (Administrativní registr ekonomických subjektů)",
                    registry_url: "https://mf.gov.cz/cs/ministerstvo/informacni-systemy/ares",
                    api_url: "", icon: "fa-solid fa-building-columns",
                    status: "ok", status_text: "Všechny údaje v ARES jsou aktuální",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["IČO: 12345678 – platné", "Sídlo: Dlouhá 15, Praha 1 – odpovídá", "Jednatel: Jan Novák – zapsán", "Předmět podnikání: aktivní"]
                },
                {
                    id: "dph_registry", title: "Spolehlivost plátce DPH",
                    description: "Ověření spolehlivosti plátce DPH a registrovaných bankovních účtů.",
                    registry_name: "Registr DPH (Portál MOJE daně)",
                    registry_url: "https://financnisprava.gov.cz/registr-dph",
                    api_url: "", icon: "fa-solid fa-file-invoice-dollar",
                    status: "ok", status_text: "Plátce je spolehlivý, účet zveřejněn",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Stav plátce: spolehlivý", "Registrace k DPH: platná", "Zveřejněný účet: CZ65 0800...", "Nespolehlivost: NE"]
                },
                {
                    id: "isds", title: "Datové schránky",
                    description: "Sledování nových zpráv v datové schránce a hlídání lhůt doručení.",
                    registry_name: "ISDS (Informační systém datových schránek)",
                    registry_url: "https://mojedatovaschranka.cz",
                    api_url: "", icon: "fa-solid fa-envelope-open-text",
                    status: "warning", status_text: "2 nepřečtené zprávy – lhůta vyprší za 3 dny",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Celkem zpráv: 47", "Nepřečtené: 2", "Nejstarší nepřečtená: od FÚ Praha 1", "⚠ Fikce doručení za 3 dny"]
                },
                {
                    id: "isir", title: "Insolvence a úpadek firem",
                    description: "Prověřování obchodních partnerů v insolvenčním rejstříku.",
                    registry_name: "Insolvenční rejstřík (ISIR)",
                    registry_url: "https://isir.justice.cz",
                    api_url: "", icon: "fa-solid fa-triangle-exclamation",
                    status: "ok", status_text: "Žádné insolvenční řízení nenalezeno",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Vlastní firma: bez nálezu", "Sledovaní partneři: 5", "Partner s nálezem: 0", "Poslední kontrola: dnes"]
                },
                {
                    id: "e_sbirka", title: "Legislativní změny na míru",
                    description: "Automatické sledování nových zákonů a novel relevantních pro obor podnikání.",
                    registry_name: "Sbírka zákonů a mezinárodních smluv (e-Sbírka)",
                    registry_url: "https://e-sbirka.cz",
                    api_url: "", icon: "fa-solid fa-scale-balanced",
                    status: "info", status_text: "Novela zákona o DPH účinná od 1.1. příštího roku",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Sledovaných předpisů: 12", "Nové: Novela zák. 235/2004 Sb.", "Zákoník práce: beze změn", "Živnostenský zákon: beze změn"]
                },
                {
                    id: "vies", title: "Zahraniční DPH a subjekty v EU",
                    description: "Ověřování DIČ zahraničních partnerů v systému VIES.",
                    registry_name: "VIES (VAT Information Exchange System)",
                    registry_url: "https://ec.europa.eu/taxation_customs/vies",
                    api_url: "", icon: "fa-solid fa-earth-europe",
                    status: "ok", status_text: "Všichni EU partneři mají platné DIČ",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Sledovaných EU partnerů: 3", "DE123456789 – platné", "SK2020123456 – platné", "AT U12345678 – platné"]
                },
                {
                    id: "partner_check", title: "Prověřování partnerů",
                    description: "Kontinuální monitoring bonity a insolvence klíčových obchodních partnerů.",
                    registry_name: "ISIR + ARES (křížová kontrola)",
                    registry_url: "https://isir.justice.cz",
                    api_url: "", icon: "fa-solid fa-user-shield",
                    status: "warning", status_text: "1 partner vykazuje zhoršenou bonitu",
                    last_checked: new Date().toLocaleString('cs-CZ'),
                    details: ["Sledovaných partnerů: 5", "⚠ ABC Trading s.r.o. – pokles bonity", "XYZ Tech a.s. – bez nálezu", "DEF Logistika s.r.o. – bez nálezu"]
                }
            ]
        };
    }

    // Header nav scroll-to
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.getAttribute('data-target');
            const el = document.getElementById(target);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
