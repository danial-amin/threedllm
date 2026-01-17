// ThreeDLLM Frontend Application

const API_BASE = '/api';

// Quality presets
const QUALITY_PRESETS = {
    fast: { steps: 64, guidanceScale: 15.0 },
    balanced: { steps: 100, guidanceScale: 17.5 },
    high: { steps: 128, guidanceScale: 20.0 }
};

// DOM elements
const generateForm = document.getElementById('generateForm');
const generateBtn = document.getElementById('generateBtn');
const statusCard = document.getElementById('statusCard');
const resultCard = document.getElementById('resultCard');
const statusText = document.getElementById('statusText');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');
const errorMessage = document.getElementById('errorMessage');
const downloadLink = document.getElementById('downloadLink');

let currentTaskId = null;
let pollInterval = null;

// Update quality preset
function updateQualityPreset() {
    const qualitySelect = document.getElementById('quality');
    const stepsInput = document.getElementById('steps');
    const guidanceInput = document.getElementById('guidanceScale');
    const stepsGroup = document.getElementById('stepsGroup');
    const guidanceGroup = document.getElementById('guidanceScaleGroup');
    
    const preset = qualitySelect.value;
    
    if (preset === 'custom') {
        stepsGroup.style.display = 'block';
        guidanceGroup.style.display = 'block';
    } else {
        const config = QUALITY_PRESETS[preset];
        stepsInput.value = config.steps;
        guidanceInput.value = config.guidanceScale;
        stepsGroup.style.display = 'block';
        guidanceGroup.style.display = 'block';
    }
}

// Form submission
generateForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Reset UI
    hideAllCards();
    errorMessage.classList.add('hidden');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    // Get form data
    const formData = new FormData(generateForm);
    
    // Log the generator being sent
    const generatorValue = formData.get('generator');
    console.log('Sending generation request with generator:', generatorValue);
    console.log('All form data:', Object.fromEntries(formData.entries()));
    
    try {
        // Submit generation request
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start generation');
        }
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // Show status card
        statusCard.classList.remove('hidden');
        
        // Start polling for status
        startPolling(currentTaskId);
        
    } catch (error) {
        showError(error.message);
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate 3D Object';
    }
});

// Poll task status
function startPolling(taskId) {
    // Poll immediately
    checkStatus(taskId);
    
    // Then poll every 2 seconds
    pollInterval = setInterval(() => {
        checkStatus(taskId);
    }, 2000);
}

async function checkStatus(taskId) {
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch task status');
        }
        
        const status = await response.json();
        updateStatus(status);
        
        // Stop polling if task is completed or failed
        if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate 3D Object';
            
            if (status.status === 'completed') {
                showResult(status.result_url);
            }
        }
        
    } catch (error) {
        clearInterval(pollInterval);
        showError(error.message);
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate 3D Object';
    }
}

function updateStatus(status) {
    // Update status text
    statusText.textContent = status.status;
    statusText.className = status.status;
    
    // Update progress
    const progress = status.progress || 0;
    progressFill.style.width = `${progress * 100}%`;
    progressText.textContent = `${Math.round(progress * 100)}%`;
    
    // Update message
    statusMessage.textContent = status.message;
    
    // Show error if any
    if (status.error) {
        errorMessage.textContent = `Error: ${status.error}`;
        errorMessage.classList.remove('hidden');
    } else {
        errorMessage.classList.add('hidden');
    }
}

function showResult(resultUrl) {
    resultCard.classList.remove('hidden');
    downloadLink.href = resultUrl;
    
    // Extract filename from URL
    const filename = resultUrl.split('/').pop();
    downloadLink.download = filename;
    
    // Extract format from filename - handle edge cases
    let format = 'obj'; // default
    if (filename && filename.includes('.')) {
        const parts = filename.split('.');
        if (parts.length > 1) {
            format = parts[parts.length - 1].toLowerCase().trim();
        }
    }
    
    // Validate format
    const validFormats = ['obj', 'ply', 'stl', 'xyz'];
    if (!validFormats.includes(format)) {
        console.warn(`Unknown format "${format}", defaulting to OBJ`);
        format = 'obj';
    }
    
    console.log('Loading mesh with format:', format, 'from URL:', resultUrl);
    
    // Load mesh in viewer
    if (typeof loadMeshInViewer === 'function') {
        loadMeshInViewer(resultUrl, format);
    } else {
        console.error('loadMeshInViewer function not available');
    }
}

function showError(message) {
    errorMessage.textContent = `Error: ${message}`;
    errorMessage.classList.remove('hidden');
    statusCard.classList.remove('hidden');
}

function hideAllCards() {
    statusCard.classList.add('hidden');
    resultCard.classList.add('hidden');
}

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const health = await response.json();
        
        if (!health.generator_available) {
            showError('3D generator is not available. Please check your installation.');
        }
        
        if (health.vlm_available === false) {
            console.warn('VLM is not available. VLM enhancement will be disabled.');
        }
    } catch (error) {
        console.error('Failed to check API health:', error);
    }
}

// Initialize
checkHealth();
updateQualityPreset(); // Set initial preset values

// Wait for Three.js modules to be ready
function waitForThreeModules(callback, maxWait = 10000) {
    const startTime = Date.now();
    
    const checkModules = () => {
        if (window.threeModulesReady && 
            window.THREE_OBJLoader && 
            window.THREE_PLYLoader && 
            window.THREE_STLLoader && 
            window.THREE_OrbitControls) {
            console.log('Three.js modules confirmed ready');
            callback();
        } else if (Date.now() - startTime < maxWait) {
            setTimeout(checkModules, 100);
        } else {
            console.error('Three.js modules failed to load within timeout');
            alert('Three.js modules failed to load. Please refresh the page.');
        }
    };
    
    // Also listen for the custom event
    window.addEventListener('threeModulesReady', callback, { once: true });
    
    // Start checking
    checkModules();
}

// Initialize viewer when result card becomes visible
const observer = new MutationObserver(() => {
    if (!resultCard.classList.contains('hidden')) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            if (typeof initViewer === 'function' && !viewer) {
                waitForThreeModules(() => {
                    initViewer();
                });
            }
        }, 100);
    }
});
observer.observe(resultCard, { attributes: true, attributeFilter: ['class'] });

// Reset view button
const resetViewBtn = document.getElementById('resetViewBtn');
if (resetViewBtn) {
    resetViewBtn.addEventListener('click', () => {
        if (typeof resetViewerView === 'function') {
            resetViewerView();
        }
    });
}