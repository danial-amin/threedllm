// ThreeDLLM Frontend Application

const API_BASE = '/api';

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
