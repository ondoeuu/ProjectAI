document.addEventListener('DOMContentLoaded', () => {
    
    // --- UI Elements ---
    const stepLanding = document.getElementById('step-landing');
    const stepPortal = document.getElementById('step-portal');
    const stepIntent = document.getElementById('step-intent');
    const stepProcessing = document.getElementById('step-processing');
    const stepProposal = document.getElementById('step-proposal');
    const stepSubscription = document.getElementById('step-subscription');
    const stepDashboard = document.getElementById('step-dashboard');

    const btnLogin = document.getElementById('btn-login');
    const btnNewCompany = document.getElementById('btn-new-company');
    const inputIntent = document.getElementById('input-intent');
    const btnSubmitIntent = document.getElementById('btn-submit-intent');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnCancel = document.getElementById('btn-cancel');
    const headerNav = document.getElementById('header-nav');

    // Globální data
    let currentUser = null;
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

    // 1. Login (BankID) -> Načtení Portálu
    btnLogin.addEventListener('click', async () => {
        btnLogin.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Přihlašuji přes BankID...';
        try {
            const res = await fetch('/api/login', { method: 'POST' });
            if(res.ok) {
                currentUser = await res.json();
                document.getElementById('portal-user-name').innerText = currentUser.name;
                await loadPortalCompanies();
                showStep(stepPortal);
            }
        } catch(e) {
            console.error("Login failed", e);
        }
    });

    // 2. Klientský portál - Načtení firem
    async function loadPortalCompanies() {
        try {
            const res = await fetch('/api/companies');
            const companies = await res.json();
            const container = document.getElementById('portal-companies');
            container.innerHTML = '';
            
            if (companies.length === 0) {
                container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 2rem;">Zatím nemáte žádné firmy. Založte svou první!</div>`;
            } else {
                companies.forEach(c => {
                    const card = document.createElement('div');
                    card.className = 'glass-card';
                    card.style.padding = '1.5rem';
                    card.style.cursor = 'pointer';
                    card.style.transition = 'transform 0.2s';
                    card.onmouseover = () => card.style.transform = 'translateY(-5px)';
                    card.onmouseout = () => card.style.transform = 'translateY(0)';
                    
                    const tasksStatus = c.tasks_total > 0 ? `<div style="margin-top: 1rem; font-size: 0.85rem;"><i class="fa-solid fa-list-check" style="color:var(--warning)"></i> Čekajících úkolů: ${c.tasks_total - c.tasks_completed}</div>` : '';
                    
                    card.innerHTML = `
                        <h3 style="margin-bottom: 0.5rem;"><i class="fa-solid fa-building" style="color: var(--primary)"></i> ${c.name}</h3>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">IČO: ${c.ico || 'Čeká na přidělení'}</p>
                        <p style="color: var(--text-muted); font-size: 0.9rem;">Obor: ${c.business_area}</p>
                        <div style="margin-top: 1rem;"><span class="badge success">${c.status}</span></div>
                        ${tasksStatus}
                    `;
                    
                    // Po kliknutí otevře dashboard firmy
                    card.addEventListener('click', () => loadCompanyDashboard(c.id));
                    container.appendChild(card);
                });
            }
        } catch (e) {
            console.error("Chyba při načítání firem", e);
        }
    }

    // 3. Založení nové firmy -> Intent
    btnNewCompany.addEventListener('click', () => {
        showStep(stepIntent);
        inputIntent.value = "";
        inputIntent.focus();
    });

    // 4. Intent -> Processing -> API Call -> Proposal
    async function processIntent() {
        const intentVal = inputIntent.value.trim();
        if(!intentVal) return;

        showStep(stepProcessing);
        currentProposal = null; // reset předchozího stavu
        
        // Slib pro dokončení animace
        const animPromise = new Promise(resolve => runAIProcessing(resolve));
        
        // Slib pro API požadavek
        const fetchPromise = fetch('/api/onboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intent_text: intentVal })
        }).then(res => {
            if (!res.ok) throw new Error("Server error");
            return res.json();
        }).catch(error => {
            console.error("Chyba API", error);
            return null;
        });

        // Počkáme, až se dokončí animace i načítání dat
        const [_, proposal] = await Promise.all([animPromise, fetchPromise]);
        
        if (proposal) {
            currentProposal = proposal;
            populateProposal(currentProposal);
        }
        showStep(stepProposal);
    }

    btnSubmitIntent.addEventListener('click', processIntent);
    inputIntent.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') processIntent();
    });

    function runAIProcessing(onComplete) {
        const steps = document.querySelectorAll('.proc-step');
        
        // Reset stavu pro případ, že to běží opakovaně
        steps.forEach(s => {
            s.classList.remove('active-step', 'done-step');
            s.classList.add('pending');
            if (s.innerHTML.includes('fa-check-circle')) {
                s.innerHTML = s.innerHTML.replace('fa-check-circle', 'fa-circle-notch fa-spin');
            }
        });

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
                    if(onComplete) onComplete();
                }, 600);
            }
        }, 1200);
    }

    function populateProposal(data) {
        document.getElementById('prop-explanation').innerText = data.explanation;
        document.getElementById('prop-company-name-input').value = data.company_name;
        document.getElementById('prop-business-area').innerText = data.business_area;

        updateBadgeStatus(data.status === "MISSING_DATA" ? false : true);

        const reqContainer = document.getElementById('prop-requirements');
        reqContainer.innerHTML = '';
        data.requirements.forEach(req => {
            const aiBadge = req.ai_detected ? `<span class="badge ai-badge" style="margin-left: 0.5rem; background: rgba(56, 189, 248, 0.2); color: var(--primary); border: 1px solid var(--primary);"><i class="fa-solid fa-wand-magic-sparkles"></i> Odhaleno AI</span>` : '';
            const sourceInfo = req.source_law ? `<p style="font-size: 0.8rem; color: var(--primary); margin-top: 0.5rem;"><i class="fa-solid fa-scale-balanced"></i> Zdroj: ${req.source_law}</p>` : '';
            reqContainer.innerHTML += `<li class="req-item"><h4>${req.title} ${aiBadge}</h4><p>${req.description}</p>${sourceInfo}</li>`;
        });

        const dutiesContainer = document.getElementById('prop-duties');
        dutiesContainer.innerHTML = '';
        data.immediate_duties.forEach(duty => {
            const aiBadge = duty.ai_detected ? `<span class="badge ai-badge" style="margin-left: 0.5rem; background: rgba(56, 189, 248, 0.2); color: var(--primary); border: 1px solid var(--primary);"><i class="fa-solid fa-wand-magic-sparkles"></i> Odhaleno AI</span>` : '';
            const sourceInfo = duty.source_law ? `<p style="font-size: 0.8rem; color: var(--primary); margin-top: 0.5rem;"><i class="fa-solid fa-scale-balanced"></i> Zdroj: ${duty.source_law}</p>` : '';
            dutiesContainer.innerHTML += `
                <div class="duty-card">
                    <h4>${duty.title} ${aiBadge}</h4>
                    <p>${duty.description}</p>
                    <span class="deadline"><i class="fa-regular fa-clock"></i> ${duty.deadline}</span>
                    ${sourceInfo}
                </div>`;
        });
    }

    function updateBadgeStatus(isAvailable) {
        const badge = document.getElementById('prop-name-status');
        const confirmBtn = document.getElementById('btn-confirm');
        const chk = document.getElementById('chk-responsibility');
        
        if (!isAvailable) {
            badge.className = "badge danger";
            badge.innerText = "Obsazené";
            confirmBtn.disabled = true;
            confirmBtn.style.opacity = "0.5";
            confirmBtn.innerText = "Nelze založit - jméno obsazeno";
        } else {
            badge.className = "badge success";
            badge.innerText = "Volné";
            confirmBtn.innerText = "Schválit a Založit elektronicky";
            
            // Checkbox logic
            if (chk.checked) {
                confirmBtn.disabled = false;
                confirmBtn.style.opacity = "1";
            } else {
                confirmBtn.disabled = true;
                confirmBtn.style.opacity = "0.5";
            }
            
            chk.addEventListener('change', () => {
                if (chk.checked) {
                    confirmBtn.disabled = false;
                    confirmBtn.style.opacity = "1";
                } else {
                    confirmBtn.disabled = true;
                    confirmBtn.style.opacity = "0.5";
                }
            });
        }
    }

    // Nové ověření jména
    document.getElementById('btn-recheck-name').addEventListener('click', async () => {
        const newName = document.getElementById('prop-company-name-input').value.trim();
        if (!newName) return;
        
        const btn = document.getElementById('btn-recheck-name');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        
        try {
            const res = await fetch('/api/check-name', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ company_name: newName })
            });
            const data = await res.json();
            
            updateBadgeStatus(data.available);
            
            if (data.available && currentProposal) {
                currentProposal.company_name = newName;
                currentProposal.status = "READY_FOR_REVIEW";
            }
        } catch (e) {
            console.error(e);
        }
        btn.innerHTML = 'Ověřit';
    });

    // 5. Potvrzení Návrhu -> Výběr Předplatného
    btnConfirm.addEventListener('click', () => {
        showStep(stepSubscription);
    });

    // 5.5 Výběr Předplatného -> Uložení DB -> Načtení Dashboardu
    document.querySelectorAll('.btn-plan').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const plan = e.currentTarget.dataset.plan;
            currentProposal.plan = plan; // Uložíme zvolený plán
            
            const originalHtml = e.currentTarget.innerHTML;
            e.currentTarget.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Zakládám...';
            e.currentTarget.disabled = true;
            
            try {
                const res = await fetch('/api/companies', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentProposal)
                });
                const data = await res.json();
                await loadCompanyDashboard(data.company_id);
            } catch (e) {
                console.error(e);
                e.currentTarget.innerHTML = originalHtml;
                e.currentTarget.disabled = false;
            }
        });
    });

    btnCancel.addEventListener('click', () => {
        showStep(stepPortal); // Zrušení vrátí do portálu
    });

    // 6. DASHBOARD LOGIC a Načítání firemních úkolů z DB
    async function loadCompanyDashboard(companyId) {
        try {
            const res = await fetch(`/api/companies/${companyId}`);
            if(!res.ok) throw new Error("Nenalezeno");
            const companyData = await res.json();
            
            // Získáme mock monitoring data pro danou firmu (jen vizuální)
            const dRes = await fetch(`/api/dashboard?company_name=${encodeURIComponent(companyData.name)}&ico=${companyData.ico}`);
            currentDashboard = await dRes.json();
            
            populateDashboard(currentDashboard);
            renderTasks(companyData.tasks);
            
            headerNav.style.display = 'flex';
            showStep(stepDashboard);
        } catch(e) {
            console.error("Error loading dashboard", e);
        }
    }

    function renderTasks(tasks) {
        const container = document.getElementById('dash-tasks-container');
        container.innerHTML = '';
        
        if (tasks.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted);">Všechny povinnosti jsou aktuálně vyřešeny.</p>';
            return;
        }

        tasks.forEach(t => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'glass-card';
            taskDiv.style.padding = '1.5rem';
            taskDiv.style.display = 'flex';
            taskDiv.style.justifyContent = 'space-between';
            taskDiv.style.alignItems = 'center';
            taskDiv.style.borderLeft = t.is_completed ? '4px solid var(--success)' : '4px solid var(--warning)';
            
            const actionHtml = t.is_completed ? 
                `<span style="color: var(--success); font-weight: bold;"><i class="fa-solid fa-check-double"></i> Vyřešeno</span>` :
                (t.can_automate ? 
                    `<button class="primary-btn pulse-anim" onclick="executeTask(${t.id}, this)" style="padding: 0.5rem 1rem; font-size: 0.9rem;">
                        <i class="fa-solid fa-robot"></i> Vyřešit za mě
                    </button>` : 
                    `<span style="color: var(--text-muted);"><i class="fa-solid fa-person-digging"></i> Vyžaduje vaši součinnost</span>`);

            const aiBadge = t.ai_detected ? `<span class="badge ai-badge" style="margin-left: 0.5rem; background: rgba(56, 189, 248, 0.2); color: var(--primary); border: 1px solid var(--primary);"><i class="fa-solid fa-wand-magic-sparkles"></i> Odhaleno AI</span>` : '';
            const sourceInfo = t.source_law ? `<p style="font-size: 0.8rem; color: var(--primary); margin-top: 0.5rem;"><i class="fa-solid fa-scale-balanced"></i> Zdroj: ${t.source_law}</p>` : '';

            taskDiv.innerHTML = `
                <div>
                    <h4 style="margin-bottom: 0.3rem; font-size: 1.1rem; color: ${t.is_completed ? 'var(--text-muted)' : 'white'};">${t.title} ${aiBadge}</h4>
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 0.5rem;">${t.description}</p>
                    <span class="deadline" style="background: ${t.is_completed ? 'rgba(255,255,255,0.05)' : ''}"><i class="fa-regular fa-clock"></i> ${t.deadline}</span>
                    ${sourceInfo}
                </div>
                <div class="task-action">
                    ${actionHtml}
                </div>
            `;
            container.appendChild(taskDiv);
        });
    }

    // Tlačítko pro simulaci posunu času
    document.getElementById('btn-simulate').addEventListener('click', async (e) => {
        const btn = e.currentTarget;
        const origHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Simuluji...';
        
        try {
            const types = ["new_law", "deadline"];
            const randomType = types[Math.floor(Math.random() * types.length)];
            
            // Reload company to get latest state
            const cRes = await fetch(`/api/companies`);
            const companies = await cRes.json();
            const latestCompany = companies[companies.length - 1]; // We take the last created company

            const res = await fetch('/api/simulate-event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_id: latestCompany.id, event_type: randomType })
            });
            const data = await res.json();
            
            if(data.status === 'success') {
                // Překreslíme tasky
                const updatedRes = await fetch(`/api/companies/${latestCompany.id}`);
                const updatedCompany = await updatedRes.json();
                renderTasks(updatedCompany.tasks);
                
                // Zvýšíme counter alertů
                const countEl = document.getElementById('dash-alerts-count');
                countEl.innerText = parseInt(countEl.innerText) + 1;
                document.getElementById('dash-alerts-pill').style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                document.getElementById('dash-alerts-pill').style.color = 'var(--danger)';
            }
        } catch(e) {
            console.error(e);
        }
        btn.innerHTML = origHtml;
    });

    // Globální funkce pro zavolání z inline onclick
    window.executeTask = async function(taskId, btnElement) {
        btnElement.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Zpracovávám...';
        btnElement.classList.remove('pulse-anim');
        btnElement.disabled = true;

        try {
            const res = await fetch(`/api/tasks/${taskId}/execute`, { method: 'POST' });
            if(res.ok) {
                // Úspěšně vyřešeno, vizuálně upravíme
                const actionDiv = btnElement.parentElement;
                actionDiv.innerHTML = `<span style="color: var(--success); font-weight: bold;"><i class="fa-solid fa-check-double"></i> Vyřešeno AI</span>`;
                actionDiv.parentElement.style.borderLeftColor = 'var(--success)';
                const title = actionDiv.parentElement.querySelector('h4');
                title.style.color = 'var(--text-muted)';
            }
        } catch(e) {
            console.error(e);
            btnElement.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Chyba';
        }
    };

    function populateDashboard(data) {
        document.getElementById('dash-company-name').innerText = data.company_name;
        document.getElementById('dash-ico').innerText = data.ico || "12345678";
        document.getElementById('dash-last-scan').innerText = data.last_full_scan;
        
        const alertsEl = document.getElementById('dash-alerts-count');
        const alertsPill = document.getElementById('dash-alerts-pill');
        if(alertsEl && alertsPill) {
            alertsEl.innerText = data.alerts_count;
            if (data.alerts_count > 0) alertsPill.classList.add('has-alerts');
            else alertsPill.classList.remove('has-alerts');
        }

        const limitsContainer = document.getElementById('dash-limits');
        if(limitsContainer && data.legal_limits) {
            limitsContainer.innerHTML = '';
            data.legal_limits.forEach((limit, idx) => {
                const percentage = Math.min((limit.current_value / limit.limit_value) * 100, 100);
                const statusClass = limit.status; 
                limitsContainer.innerHTML += `
                    <div class="limit-card glass-card slide-up" style="animation-delay: ${idx * 0.1}s">
                        <div class="limit-header">
                            <div class="limit-icon ${statusClass}"><i class="${limit.icon}"></i></div>
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
        }

        const monitoringContainer = document.getElementById('dash-monitoring');
        if(monitoringContainer && data.monitoring_areas) {
            monitoringContainer.innerHTML = '';
            data.monitoring_areas.forEach((area, idx) => {
                const statusClass = area.status;
                const detailsHtml = area.details.map(d => `<li>${d}</li>`).join('');
                monitoringContainer.innerHTML += `
                    <div class="monitor-card glass-card slide-up" style="animation-delay: ${idx * 0.08}s">
                        <div class="monitor-header">
                            <div class="monitor-icon ${statusClass}"><i class="${area.icon}"></i></div>
                            <div class="monitor-status-dot ${statusClass}" title="${getStatusLabel(area.status)}"></div>
                        </div>
                        <h3 class="monitor-title">${area.title}</h3>
                        <p class="monitor-registry">${area.registry_name}</p>
                        <p class="monitor-description">${area.description}</p>
                        <div class="monitor-status-bar ${statusClass}">
                            <i class="fa-solid ${getStatusIcon(area.status)}"></i>
                            <span>${area.status_text}</span>
                        </div>
                        <ul class="monitor-details">${detailsHtml}</ul>
                        <div class="monitor-footer">
                            <span class="monitor-time"><i class="fa-regular fa-clock"></i> ${area.last_checked}</span>
                            <a href="${area.registry_url}" target="_blank" class="monitor-link"><i class="fa-solid fa-arrow-up-right-from-square"></i></a>
                        </div>
                    </div>
                `;
            });
        }

        setTimeout(() => animateProgressBars(), 300);
    }

    function animateProgressBars() {
        document.querySelectorAll('.progress-fill').forEach(bar => {
            const target = bar.getAttribute('data-target');
            setTimeout(() => bar.style.width = target + '%', 100);
        });
    }

    function getStatusLabel(status) {
        const labels = { 'ok': 'V pořádku', 'warning': 'Upozornění', 'danger': 'Kritické', 'info': 'Info' };
        return labels[status] || status;
    }

    function getStatusIcon(status) {
        const icons = { 'ok': 'fa-circle-check', 'warning': 'fa-exclamation-triangle', 'danger': 'fa-circle-xmark', 'info': 'fa-circle-info' };
        return icons[status] || 'fa-circle-info';
    }

    function formatNumber(num) {
        return num >= 1000 ? num.toLocaleString('cs-CZ') : num.toString();
    }

    // Header nav scroll-to
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.getAttribute('data-target');
            const el = document.getElementById(target);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // Zpět z dashboardu do portálu
    const btnBackToPortal = document.querySelector('.dashboard-footer .primary-btn');
    if(btnBackToPortal) {
        btnBackToPortal.onclick = (e) => {
            e.preventDefault();
            loadPortalCompanies();
            showStep(stepPortal);
            headerNav.style.display = 'none';
        };
    }
});
