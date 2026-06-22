document.addEventListener('DOMContentLoaded', () => {
    
    // --- UI Elements ---
    const stepIdentity = document.getElementById('step-identity');
    const stepIntent = document.getElementById('step-intent');
    const stepProcessing = document.getElementById('step-processing');
    const stepProposal = document.getElementById('step-proposal');
    const stepSuccess = document.getElementById('step-success');

    const btnLogin = document.getElementById('btn-login');
    const inputIntent = document.getElementById('input-intent');
    const btnSubmitIntent = document.getElementById('btn-submit-intent');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnCancel = document.getElementById('btn-cancel');

    // --- Mock Data (Simulující výstup z agent.py) ---
    const mockProposal = {
        founder_id: "user_bankid_123",
        status: "READY_FOR_REVIEW",
        company_name: "Inovace s.r.o.",
        business_area: "Vývoj software",
        immediate_duties: [
            {
                title: "Registrace k dani z příjmů (DPPO)",
                description: "Povinná registrace u finančního úřadu do 15 dnů.",
                deadline: "Do 15 dnů od vzniku"
            },
            {
                title: "Zápis do evidence skutečných majitelů",
                description: "Návrh na zápis musí být podán bez zbytečného odkladu.",
                deadline: "Bez zbytečného odkladu"
            }
        ],
        scheduled_duties: [
            { title: "Podání daňového přiznání (DPPO)", deadline: "2. května příští rok" },
            { title: "Založení účetní závěrky do sbírky listin", deadline: "31. července příští rok" }
        ],
        requirements: [
            {
                title: "Ohlášení volné živnosti",
                description: "Pro obor Vývoj software není vyžadována koncese ani prokazování odborné způsobilosti. Postačuje ohlášení."
            }
        ],
        explanation: "Všechny dostupné registry byly zkontrolovány (ARES, ROS). Název firmy 'Inovace s.r.o.' je volný. Připravil jsem návrh na založení a seznam okamžitých povinností po zápisu do Obchodního rejstříku."
    };

    // --- Navigation Logic ---
    function showStep(stepElement) {
        document.querySelectorAll('.step').forEach(el => {
            el.classList.remove('active');
            el.classList.add('hidden');
        });
        stepElement.classList.remove('hidden');
        // Malý timeout pro aplikaci CSS animací
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

    // 2. Intent -> Processing -> Proposal
    function processIntent() {
        const intentVal = inputIntent.value.trim();
        if(!intentVal) return; // Nedovolit prázdný submit

        // Zkusíme extrahovat jméno z textu pro hezčí demo
        if (intentVal.includes("Kofíčko")) {
            mockProposal.company_name = "Kofíčko s.r.o.";
            mockProposal.business_area = "Hostinská činnost";
            mockProposal.requirements = [{
                title: "Doložení odborné způsobilosti",
                description: "Pro obor Hostinská činnost (řemeslná živnost) legislativa vyžaduje doložení praxe nebo vzdělání v oboru."
            }];
        } else if (intentVal.match(/([A-Z][a-z]+ s\.r\.o\.)/)) {
            const match = intentVal.match(/([A-Z][a-z]+ s\.r\.o\.)/);
            mockProposal.company_name = match[1];
        } else if (intentVal.length > 5) {
             mockProposal.company_name = "Nová firma s.r.o.";
             mockProposal.business_area = "Volná živnost";
        }

        showStep(stepProcessing);
        runAIProcessing();
    }

    btnSubmitIntent.addEventListener('click', processIntent);
    inputIntent.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') processIntent();
    });

    // 3. AI Processing Animation
    function runAIProcessing() {
        const steps = document.querySelectorAll('.proc-step');
        let currentStep = 0;

        const interval = setInterval(() => {
            if (currentStep > 0) {
                // Dokončit předchozí
                const prev = steps[currentStep - 1];
                prev.classList.remove('active-step');
                prev.classList.add('done-step');
                prev.innerHTML = prev.innerHTML.replace('fa-circle-notch fa-spin', 'fa-check-circle');
            }

            if (currentStep < steps.length) {
                // Aktivovat aktuální
                const curr = steps[currentStep];
                curr.classList.remove('pending');
                curr.classList.add('active-step');
                currentStep++;
            } else {
                // Vše hotovo
                clearInterval(interval);
                setTimeout(() => {
                    populateProposal(mockProposal);
                    showStep(stepProposal);
                }, 800);
            }
        }, 1500); // Každý krok trvá 1.5s
    }

    // 4. Naplnění UI daty z "Backendu"
    function populateProposal(data) {
        document.getElementById('prop-explanation').innerText = data.explanation;
        document.getElementById('prop-company-name').innerText = data.company_name;
        document.getElementById('prop-business-area').innerText = data.business_area;

        // Requirements
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

        // Duties
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

    // 5. Potvrzení (Success a Scheduling)
    btnConfirm.addEventListener('click', () => {
        btnConfirm.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Zpracovávám podání...';
        
        setTimeout(() => {
            const successTasks = document.getElementById('success-scheduled');
            successTasks.innerHTML = '';
            
            mockProposal.scheduled_duties.forEach(task => {
                successTasks.innerHTML += `
                    <div style="background: rgba(0,0,0,0.2); padding: 1rem; border-radius: 8px; margin: 0.5rem auto; max-width: 400px; display: flex; justify-content: space-between; align-items: center;">
                        <span><i class="fa-solid fa-calendar text-success"></i> ${task.title}</span>
                        <span style="font-size: 0.85rem; color: #94a3b8;">${task.deadline}</span>
                    </div>
                `;
            });

            showStep(stepSuccess);
        }, 1500);
    });

    btnCancel.addEventListener('click', () => {
        location.reload();
    });
});
