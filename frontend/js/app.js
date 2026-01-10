const API_URL = "http://localhost:8000";

const AppState = {
    userId: localStorage.getItem('graph_user_id') || 1,
    selectedGenres: new Set(),
    
    setUserId: function(id) {
        this.userId = id;
        localStorage.setItem('graph_user_id', id);
        window.dispatchEvent(new Event('userChanged'));
    }
};

// --- API Calls ---

async function fetchItems() {
    try {
        const res = await fetch(`${API_URL}/items`);
        return await res.json();
    } catch (e) { return {}; }
}

async function toggleInteraction(itemId, isUnlike) {
    const method = isUnlike ? 'DELETE' : 'POST';
    try {
        const res = await fetch(`${API_URL}/interaction/`, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(AppState.userId), item_id: itemId })
        });
        return res.ok;
    } catch (e) { return false; }
}

async function fetchUserLikes() {
    try {
        const res = await fetch(`${API_URL}/interaction/${AppState.userId}`);
        return res.ok ? await res.json() : [];
    } catch (e) { return []; }
}

async function savePreferences() {
    const genres = Array.from(AppState.selectedGenres);
    await fetch(`${API_URL}/recommend/preferences`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: parseInt(AppState.userId), genres: genres })
    });
    console.log("Preferences saved:", genres);
}

async function fetchRecommendations() {
    // REMOVED: await savePreferences(); 
    // We don't save prefs here anymore. Only when buttons are clicked.
    
    try {
        const res = await fetch(`${API_URL}/recommend/${AppState.userId}?k=5`);
        return await res.json();
    } catch (e) { return null; }
}

async function fetchMetrics() {
    try {
        const res = await fetch(`${API_URL}/metrics/`);
        return await res.json();
    } catch (e) { return null; }
}

// --- Helpers ---

function updateUserIdDisplay() {
    document.querySelectorAll('.user-id-input').forEach(input => input.value = AppState.userId);
}

document.addEventListener('DOMContentLoaded', () => {
    updateUserIdDisplay();
    
    document.querySelectorAll('.user-id-input').forEach(input => {
        input.addEventListener('change', (e) => AppState.setUserId(e.target.value));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.target.blur(); 
            }
        });
    });
});