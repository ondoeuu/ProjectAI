/* -------------------------------------------------------------
 * AuraGen Javascript Application Engine
 * ------------------------------------------------------------- */

// State Management
const state = {
    selectedModel: 'flux',
    aspectRatio: '1:1',
    width: 1024,
    height: 1024,
    seed: null,
    isSeedLocked: false,
    isGenerating: false,
    history: [],
    currentGeneratedItem: null
};

// Prompt Generator Dictionaries
const promptComponents = {
    subjects: [
        "A futuristic cybernetic samurai standing in neon rain",
        "An ancient mystical library carved inside a giant redwood tree",
        "A steampunk explorer looking through a brass telescope on a cloud dock",
        "A majestic dragon made entirely of glowing bioluminescent crystal",
        "An astronaut floating in space surrounded by glowing stellar dust",
        "A cozy cottage in a magical forest with glowing mushrooms and fairy lights",
        "A hyper-detailed mechanical eye reflecting a futuristic galaxy",
        "A majestic deer with antlers made of gold and flowering vines",
        "A mythical floating island with waterfalls cascading down into the sky",
        "A cyberpunk street food vendor in a bustling Tokyo alleyway",
        "A crystalline phoenix rising from glowing cosmic embers",
        "A serene zen garden on a Martian colony under two moons"
    ],
    scenes: [
        "overlooking a glowing holographic city skyline",
        "surrounded by floating ancient runic symbols",
        "drowned in dense mystical fog with neon reflections",
        "with celestial nebulae swirling in the deep background",
        "under a dramatic sunset sky with golden cloud layers",
        "in an infinite digital void with glowing line grids",
        "during a serene snowfall with soft ambient streetlamps",
        "against a backdrop of giant orbiting ringed planets",
        "in a detailed cozy interior with sunlight filtering through blinds",
        "amidst cascading waterfalls under a bioluminescent canopy"
    ],
    styles: [
        "Highly detailed cinematic render",
        "Surreal dreamlike oil painting style",
        "Cyberpunk concept art with rich texture",
        "Stunning 3D octane render, studio grade",
        "Intricate dark fantasy digital illustration",
        "Vibrant watercolor sketch with ink outlines",
        "Atmospheric lofi anime style, warm tones",
        "Photorealistic national geographic style shot",
        "Futuristic synthwave aesthetic, high contrast",
        "Chiaroscuro dramatic fine art photography"
    ],
    lighting: [
        "volumetric light shafts cutting through the air",
        "soft golden hour illumination, warm glow",
        "intense neon backlight with cyber pink and teal accents",
        "moody side-lighting with deep dramatic shadows",
        "bioluminescent light glowing softly from within",
        "cinematic rim lighting highlighting the contours",
        "ethereal cosmic rays illuminating the scene",
        "ambient glow from neon signs reflecting on wet asphalt"
    ],
    details: [
        "8k resolution, masterpiece",
        "intricate fine detail, high dynamic range",
        "sharp focus, award winning composition",
        "photorealistic textures, raytraced reflections",
        "dramatic perspective, depth of field"
    ]
};

// UI Elements
const dom = {
    modelSelect: document.getElementById('model-select'),
    aspectCards: document.querySelectorAll('.aspect-card'),
    randomizeSeedBtn: document.getElementById('randomize-seed-btn'),
    seedInput: document.getElementById('seed-input'),
    lockSeedBtn: document.getElementById('lock-seed-btn'),
    enhancePromptChk: document.getElementById('enhance-prompt-chk'),
    promptTextarea: document.getElementById('prompt-textarea'),
    surpriseBtn: document.getElementById('surprise-btn'),
    generateBtn: document.getElementById('generate-btn'),
    
    // Display panels
    placeholderPanel: document.getElementById('display-placeholder'),
    loadingPanel: document.getElementById('display-loading'),
    resultPanel: document.getElementById('display-result'),
    generatedImg: document.getElementById('generated-img'),
    skeletonBox: document.getElementById('skeleton-box'),
    
    // Result details
    badgeModel: document.getElementById('badge-model'),
    badgeRatio: document.getElementById('badge-ratio'),
    copyUrlBtn: document.getElementById('copy-url-btn'),
    favoriteBtn: document.getElementById('favorite-btn'),
    downloadBtn: document.getElementById('download-btn'),
    
    // Gallery
    galleryGrid: document.getElementById('gallery-grid'),
    galleryEmptyState: document.getElementById('gallery-empty-state'),
    clearGalleryBtn: document.getElementById('clear-gallery-btn'),
    
    // Details Modal
    detailModal: document.getElementById('detail-modal'),
    modalOverlay: document.getElementById('modal-overlay'),
    modalCloseBtn: document.getElementById('modal-close-btn'),
    modalImg: document.getElementById('modal-img'),
    modalPromptText: document.getElementById('modal-prompt-text'),
    modalCopyPrompt: document.getElementById('modal-copy-prompt'),
    modalModelVal: document.getElementById('modal-model-val'),
    modalRatioVal: document.getElementById('modal-ratio-val'),
    modalSeedVal: document.getElementById('modal-seed-val'),
    modalDimsVal: document.getElementById('modal-dims-val'),
    modalReuseBtn: document.getElementById('modal-reuse-btn'),
    modalDownloadBtn: document.getElementById('modal-download-btn'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// Initial Setup
function initializeApp() {
    loadHistory();
    generateRandomSeed();
    setupEventListeners();
    setupPresetSuggestions();
}

// Generate Random Seed
function generateRandomSeed() {
    if (!state.isSeedLocked) {
        state.seed = Math.floor(Math.random() * 999999999) + 1;
        dom.seedInput.value = state.seed;
    }
}

// Toggle Seed Lock
function toggleSeedLock() {
    state.isSeedLocked = !state.isSeedLocked;
    if (state.isSeedLocked) {
        dom.lockSeedBtn.classList.add('locked');
        showToast('Seed locked for future generations', 'info');
    } else {
        dom.lockSeedBtn.classList.remove('locked');
        showToast('Seed unlocked (will randomize)', 'info');
        generateRandomSeed();
    }
}

// Get Random Item from Array
const getRandomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];

// Generate Random Prompt
function generateRandomPrompt() {
    const subject = getRandomItem(promptComponents.subjects);
    const scene = getRandomItem(promptComponents.scenes);
    const style = getRandomItem(promptComponents.styles);
    const light = getRandomItem(promptComponents.lighting);
    const detail = getRandomItem(promptComponents.details);
    
    const prompt = `${subject}, ${scene}, ${style.toLowerCase()}, ${light}, ${detail}`;
    dom.promptTextarea.value = prompt;
    showToast('Magical prompt materialized!', 'success');
}

// Setup Preset Suggestions Click Handlers
function setupPresetSuggestions() {
    const tags = document.querySelectorAll('.preset-tag');
    tags.forEach(tag => {
        tag.addEventListener('click', () => {
            dom.promptTextarea.value = tag.textContent + ", cinematic rendering, neon accents, highly detailed, 8k resolution";
            showToast(`Applied preset: ${tag.textContent}`, 'info');
        });
    });
}

// Event Listeners
function setupEventListeners() {
    // Model Select
    dom.modelSelect.addEventListener('change', (e) => {
        state.selectedModel = e.target.value;
    });
    
    // Aspect Cards
    dom.aspectCards.forEach(card => {
        card.addEventListener('click', () => {
            dom.aspectCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            state.aspectRatio = card.dataset.ratio;
            state.width = parseInt(card.dataset.width);
            state.height = parseInt(card.dataset.height);
            
            // Adjust skeleton dimension aspect ratio dynamically
            const [w, h] = state.aspectRatio.split(':');
            dom.skeletonBox.style.aspectRatio = `${w} / ${h}`;
        });
    });
    
    // Seed buttons
    dom.randomizeSeedBtn.addEventListener('click', () => {
        if (state.isSeedLocked) {
            showToast('Unlock seed first to randomize', 'error');
            return;
        }
        generateRandomSeed();
        showToast('New seed generated', 'info');
    });
    
    dom.lockSeedBtn.addEventListener('click', toggleSeedLock);
    
    // Prompt Actions
    dom.surpriseBtn.addEventListener('click', generateRandomPrompt);
    dom.generateBtn.addEventListener('click', generateImage);
    
    // Result Overlay Controls
    dom.copyUrlBtn.addEventListener('click', copyImageUrl);
    dom.favoriteBtn.addEventListener('click', toggleFavoriteActive);
    dom.downloadBtn.addEventListener('click', downloadCurrentImage);
    
    // Clear Gallery
    dom.clearGalleryBtn.addEventListener('click', clearGallery);
    
    // Modal controls
    dom.modalCloseBtn.addEventListener('click', closeModal);
    dom.modalOverlay.addEventListener('click', closeModal);
    dom.modalCopyPrompt.addEventListener('click', () => {
        navigator.clipboard.writeText(dom.modalPromptText.textContent)
            .then(() => showToast('Prompt copied to clipboard!', 'success'))
            .catch(() => showToast('Failed to copy prompt', 'error'));
    });
    dom.modalReuseBtn.addEventListener('click', reuseParameters);
}

// Enhance Prompt with default modifiers based on checkmark
function buildFinalPrompt(basePrompt) {
    if (!dom.enhancePromptChk.checked) {
        return basePrompt.trim();
    }
    
    const modifiers = "epic scale, detailed texture rendering, photorealistic atmosphere, cinematic volumetric lighting, 8k depth of field";
    return `${basePrompt.trim()}, ${modifiers}`;
}

// Generate Image Function
function generateImage() {
    const rawPrompt = dom.promptTextarea.value.trim();
    if (!rawPrompt) {
        showToast('Please describe your vision first!', 'error');
        dom.promptTextarea.focus();
        return;
    }
    
    if (state.isGenerating) return;
    
    state.isGenerating = true;
    updateGeneratingUI(true);
    
    // Ensure we have a seed ready (and update UI input field)
    if (!state.isSeedLocked) {
        generateRandomSeed();
    }
    
    const finalPrompt = buildFinalPrompt(rawPrompt);
    
    // Construct Pollinations AI Image Endpoint URL
    // Format: https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&seed={seed}&model={model}&nologo=true
    const url = new URL(`https://image.pollinations.ai/prompt/${encodeURIComponent(finalPrompt)}`);
    url.searchParams.append('width', state.width);
    url.searchParams.append('height', state.height);
    url.searchParams.append('seed', state.seed);
    url.searchParams.append('nologo', 'true');
    
    if (state.selectedModel !== 'any') {
        url.searchParams.append('model', state.selectedModel);
    }
    
    // Preload image object to ensure smooth loading transition without flickers
    const tempImg = new Image();
    tempImg.src = url.toString();
    
    tempImg.onload = () => {
        // Build item metadata
        const newItem = {
            id: Date.now().toString(),
            prompt: rawPrompt,
            finalPrompt: finalPrompt,
            seed: state.seed,
            model: state.selectedModel,
            ratio: state.aspectRatio,
            width: state.width,
            height: state.height,
            imageUrl: url.toString(),
            timestamp: new Date().toLocaleTimeString(),
            isFavorite: false
        };
        
        state.currentGeneratedItem = newItem;
        
        // Update display UI
        dom.generatedImg.src = newItem.imageUrl;
        dom.badgeModel.textContent = getModelName(newItem.model);
        dom.badgeRatio.textContent = newItem.ratio;
        
        // Reset favorite state icon on newly generated image
        dom.favoriteBtn.classList.remove('active');
        dom.favoriteBtn.querySelector('svg').setAttribute('fill', 'none');
        
        state.isGenerating = false;
        updateGeneratingUI(false);
        
        // Save to local history automatically
        addToHistory(newItem);
        showToast('Aura materialized successfully!', 'success');
    };
    
    tempImg.onerror = () => {
        state.isGenerating = false;
        updateGeneratingUI(false);
        showToast('Generation failed. The neural grid timed out.', 'error');
    };
}

// UI State Updates during generation
function updateGeneratingUI(loading) {
    if (loading) {
        dom.generateBtn.disabled = true;
        dom.generateBtn.querySelector('span').textContent = 'Synthesizing...';
        
        dom.placeholderPanel.classList.add('hidden');
        dom.resultPanel.classList.add('hidden');
        dom.loadingPanel.classList.remove('hidden');
    } else {
        dom.generateBtn.disabled = false;
        dom.generateBtn.querySelector('span').textContent = 'Materialize';
        
        dom.loadingPanel.classList.add('hidden');
        dom.resultPanel.classList.remove('hidden');
    }
}

// Translate machine model tag to readable label
function getModelName(modelVal) {
    switch(modelVal) {
        case 'flux': return 'Flux Balanced';
        case 'flux-realism': return 'Flux Realism';
        case 'flux-anime': return 'Flux Anime';
        case 'flux-3d': return 'Flux 3D';
        case 'any': return 'Standard';
        default: return 'Flux';
    }
}

// Toast System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Choose appropriate SVG icon based on toast type
    let icon = '';
    if (type === 'success') {
        icon = `<svg class="toast-success-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    } else if (type === 'error') {
        icon = `<svg class="toast-error-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
    } else {
        icon = `<svg class="toast-info-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    }
    
    toast.innerHTML = `
        ${icon}
        <span>${message}</span>
    `;
    
    dom.toastContainer.appendChild(toast);
    
    // Auto remove after 3.5 seconds
    setTimeout(() => {
        toast.classList.add('removing');
        toast.addEventListener('animationend', () => {
            toast.remove();
        });
    }, 3500);
}

// Copy URL helper
function copyImageUrl() {
    if (!state.currentGeneratedItem) return;
    
    navigator.clipboard.writeText(state.currentGeneratedItem.imageUrl)
        .then(() => showToast('Image direct URL copied!', 'success'))
        .catch(() => showToast('Failed to copy URL', 'error'));
}

// Toggle Favorite active state
function toggleFavoriteActive() {
    if (!state.currentGeneratedItem) return;
    
    const heartSvg = dom.favoriteBtn.querySelector('svg');
    state.currentGeneratedItem.isFavorite = !state.currentGeneratedItem.isFavorite;
    
    if (state.currentGeneratedItem.isFavorite) {
        dom.favoriteBtn.classList.add('active');
        heartSvg.setAttribute('fill', '#ff007f');
        showToast('Added to local gallery favorites!', 'success');
    } else {
        dom.favoriteBtn.classList.remove('active');
        heartSvg.setAttribute('fill', 'none');
        showToast('Removed from favorites', 'info');
    }
    
    // Synchronize state with history array
    const histIdx = state.history.findIndex(item => item.id === state.currentGeneratedItem.id);
    if (histIdx !== -1) {
        state.history[histIdx].isFavorite = state.currentGeneratedItem.isFavorite;
        saveHistoryToStorage();
        renderGallery();
    }
}

// Download image helper converting to direct file download blob
async function downloadImageFile(imgUrl, filename) {
    try {
        showToast('Fetching file for download...', 'info');
        const response = await fetch(imgUrl);
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.URL.revokeObjectURL(blobUrl);
        showToast('Download started!', 'success');
    } catch (e) {
        // Fallback to opening in new window if fetch gets blocked by CORS
        window.open(imgUrl, '_blank');
        showToast('Opening in new tab (Direct download blocked)', 'info');
    }
}

function downloadCurrentImage() {
    if (!state.currentGeneratedItem) return;
    const cleanPromptName = state.currentGeneratedItem.prompt
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .substring(0, 30);
    
    const filename = `auragen-${cleanPromptName}-${state.currentGeneratedItem.seed}.jpg`;
    downloadImageFile(state.currentGeneratedItem.imageUrl, filename);
}

// Local Storage History Operations
function loadHistory() {
    try {
        const stored = localStorage.getItem('auragen_history');
        if (stored) {
            state.history = JSON.parse(stored);
            renderGallery();
        }
    } catch (e) {
        console.error('Error loading history: ', e);
    }
}

function saveHistoryToStorage() {
    try {
        localStorage.setItem('auragen_history', JSON.stringify(state.history));
    } catch (e) {
        console.error('Error saving history: ', e);
    }
}

function addToHistory(item) {
    // Prevent duplicate entries
    if (state.history.some(h => h.imageUrl === item.imageUrl)) return;
    
    state.history.unshift(item);
    
    // Limit to 30 history elements to save space
    if (state.history.length > 30) {
        state.history.pop();
    }
    
    saveHistoryToStorage();
    renderGallery();
}

function deleteHistoryItem(id, event) {
    if (event) event.stopPropagation(); // Prevent opening modal
    
    state.history = state.history.filter(item => item.id !== id);
    saveHistoryToStorage();
    renderGallery();
    showToast('Creation removed from gallery history', 'info');
}

function clearGallery() {
    if (state.history.length === 0) return;
    
    if (confirm('Are you sure you want to clear your local creations gallery?')) {
        state.history = [];
        saveHistoryToStorage();
        renderGallery();
        showToast('Gallery cleared', 'info');
    }
}

// Gallery rendering
function renderGallery() {
    dom.galleryGrid.querySelectorAll('.gallery-item').forEach(el => el.remove());
    
    if (state.history.length === 0) {
        dom.galleryEmptyState.classList.remove('hidden');
        return;
    }
    
    dom.galleryEmptyState.classList.add('hidden');
    
    state.history.forEach(item => {
        const gridItem = document.createElement('div');
        gridItem.className = 'gallery-item';
        
        // Favorite indicator check
        const favIndicator = item.isFavorite 
            ? `<div style="position:absolute; top:8px; left:8px; z-index:2; background:#ff007f; border-radius:50%; width:8px; height:8px; box-shadow:0 0 6px #ff007f;"></div>`
            : '';
            
        gridItem.innerHTML = `
            ${favIndicator}
            <img class="gallery-img" src="${item.imageUrl}" alt="${item.prompt}" loading="lazy">
            <div class="gallery-overlay">
                <p class="gallery-prompt">${item.prompt}</p>
                <div class="gallery-actions-footer">
                    <span class="gallery-model-label">${getModelName(item.model)}</span>
                    <button class="gallery-item-delete" title="Delete Artwork">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </div>
        `;
        
        // Open details modal click event
        gridItem.addEventListener('click', () => openModal(item));
        
        // Delete button click event
        const delBtn = gridItem.querySelector('.gallery-item-delete');
        delBtn.addEventListener('click', (e) => deleteHistoryItem(item.id, e));
        
        dom.galleryGrid.appendChild(gridItem);
    });
}

// Modal View Functions
let currentModalItem = null;

function openModal(item) {
    currentModalItem = item;
    dom.modalImg.src = item.imageUrl;
    dom.modalPromptText.textContent = item.prompt;
    dom.modalModelVal.textContent = getModelName(item.model);
    dom.modalRatioVal.textContent = item.ratio;
    dom.modalSeedVal.textContent = item.seed;
    dom.modalDimsVal.textContent = `${item.width}x${item.height} px`;
    
    // Bind direct link download to modal button
    dom.modalDownloadBtn.onclick = (e) => {
        e.preventDefault();
        const cleanPromptName = item.prompt
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .substring(0, 30);
        const filename = `auragen-${cleanPromptName}-${item.seed}.jpg`;
        downloadImageFile(item.imageUrl, filename);
    };
    
    dom.detailModal.classList.remove('hidden');
}

function closeModal() {
    dom.detailModal.classList.add('hidden');
    currentModalItem = null;
}

// Reuse prompt and variables in the main controls
function reuseParameters() {
    if (!currentModalItem) return;
    
    const item = currentModalItem;
    
    // Restore Model selector
    dom.modelSelect.value = item.model;
    state.selectedModel = item.model;
    
    // Restore Aspect Ratio
    state.aspectRatio = item.ratio;
    state.width = item.width;
    state.height = item.height;
    
    dom.aspectCards.forEach(card => {
        if (card.dataset.ratio === item.ratio) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
    const [w, h] = item.ratio.split(':');
    dom.skeletonBox.style.aspectRatio = `${w} / ${h}`;
    
    // Restore Seed
    state.seed = item.seed;
    dom.seedInput.value = item.seed;
    
    // Enable seed lock automatically so they can reuse it
    state.isSeedLocked = true;
    dom.lockSeedBtn.classList.add('locked');
    
    // Restore Prompt
    dom.promptTextarea.value = item.prompt;
    
    closeModal();
    showToast('Loaded configuration to workspace controls!', 'success');
}

// Run app
document.addEventListener('DOMContentLoaded', initializeApp);
