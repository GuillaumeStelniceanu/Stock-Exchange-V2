// static/js/main.js
const CONFIG = {
    API_BASE_URL: window.location.origin,
    DEBOUNCE_DELAY: 300,
    MAX_SUGGESTIONS: 10
};

class ApiService {
    static async searchTickers(query) {
        if (query.length < 2) return [];
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('Search error:', error);
            return [];
        }
    }

    static async getQuote(ticker) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/quote/${ticker}`);
            return await response.json();
        } catch (error) {
            console.error('Quote error:', error);
            return null;
        }
    }
}

// Initialize theme
document.addEventListener('DOMContentLoaded', function() {
    const theme = localStorage.getItem('theme');
    if (theme === 'light') {
        document.body.classList.add('light-mode');
    }
});