const API_URL = "http://localhost:8000";

// --- State Management ---
const AppState = {
    userId: localStorage.getItem('graph_user_id') || 1,
    
    setUserId: function(id) {
        this.userId = id;
        localStorage.setItem('graph_user_id', id);
        // Dispatch event so other parts of UI can update
        window.dispatchEvent(new Event('userChanged'));
    }
};

// --- API Interactions ---

async function fetchItems() {
    try {
        const res = await fetch(`${API_URL}/items`);
        return await res.json();
    } catch (e) {
        console.error("API Error:", e);
        return {};
    }
}

async function logInteraction(itemId) {
    const userId = AppState.userId;
    try {
        const res = await fetch(`${API_URL}/interaction/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(userId), item_id: itemId })
        });
        const data = await res.json();
        console.log("Interaction Logged:", data);
        return true;
    } catch (e) {
        alert("Failed to log interaction. Is backend running?");
        return false;
    }
}

async function fetchRecommendations() {
    const userId = AppState.userId;
    try {
        const res = await fetch(`${API_URL}/recommend/${userId}?k=5`);
        return await res.json();
    } catch (e) {
        console.error("Rec Error:", e);
        return null;
    }
}

async function fetchMetrics() {
    try {
        const res = await fetch(`${API_URL}/metrics/`);
        return await res.json();
    } catch (e) {
        return null;
    }
}

// --- Shared UI Helpers ---

function updateUserIdDisplay() {
    const inputs = document.querySelectorAll('.user-id-input');
    inputs.forEach(input => input.value = AppState.userId);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateUserIdDisplay();
    
    // Listen for manual changes to inputs
    document.querySelectorAll('.user-id-input').forEach(input => {
        input.addEventListener('change', (e) => {
            AppState.setUserId(e.target.value);
        });
    });
});