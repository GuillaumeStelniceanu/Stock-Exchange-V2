// static/js/main.js
// Configuration globale
const CONFIG = {
    API_BASE_URL: window.location.origin,
    DEBOUNCE_DELAY: 300,
    MAX_SUGGESTIONS: 10
};

// Gestionnaire d'état
class AppState {
    constructor() {
        this.currentTicker = null;
        this.currentPeriod = '6mo';
        this.isLoading = false;
    }
    
    setLoading(state) {
        this.isLoading = state;
        const loader = document.getElementById('global-loader');
        if (loader) {
            loader.style.display = state ? 'flex' : 'none';
        }
    }
}

// Service API
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

// Composant de recherche
class SearchComponent {
    constructor() {
        this.input = document.getElementById('search-input');
        this.suggestions = document.getElementById('search-suggestions');
        this.debounceTimer = null;
        
        if (this.input) {
            this.initialize();
        }
    }
    
    initialize() {
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('click', this.handleClickOutside.bind(this));
    }
    
    handleInput(event) {
        clearTimeout(this.debounceTimer);
        
        this.debounceTimer = setTimeout(async () => {
            const query = event.target.value.trim();
            
            if (query.length >= 2) {
                const results = await ApiService.searchTickers(query);
                this.displaySuggestions(results);
            } else {
                this.hideSuggestions();
            }
        }, CONFIG.DEBOUNCE_DELAY);
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            this.search();
        } else if (event.key === 'Escape') {
            this.hideSuggestions();
        }
    }
    
    handleClickOutside(event) {
        if (!this.suggestions.contains(event.target) && event.target !== this.input) {
            this.hideSuggestions();
        }
    }
    
    displaySuggestions(suggestions) {
        if (suggestions.length === 0) {
            this.suggestions.innerHTML = `
                <div class="suggestion-item">
                    <span class="text-muted">Aucun résultat</span>
                </div>
            `;
            this.showSuggestions();
            return;
        }
        
        let html = '';
        suggestions.forEach((item, index) => {
            html += `
                <div class="suggestion-item" 
                     data-ticker="${item.ticker}"
                     data-index="${index}"
                     onclick="selectTicker('${item.ticker}')"
                     onmouseenter="highlightSuggestion(${index})">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong class="ticker">${item.ticker}</strong>
                            <div class="company-name text-muted">${item.name}</div>
                        </div>
                        <span class="badge bg-${item.market.toLowerCase()}">
                            ${item.market}
                        </span>
                    </div>
                </div>
            `;
        });
        
        this.suggestions.innerHTML = html;
        this.showSuggestions();
    }
    
    search() {
        const ticker = this.input.value.trim().toUpperCase();
        if (ticker) {
            window.location.href = `/analyse?ticker=${ticker}&period=${appState.currentPeriod}`;
        }
    }
    
    showSuggestions() {
        this.suggestions.style.display = 'block';
        this.suggestions.style.opacity = '1';
    }
    
    hideSuggestions() {
        this.suggestions.style.opacity = '0';
        setTimeout(() => {
            this.suggestions.style.display = 'none';
        }, 200);
    }
}

// Gestionnaire de graphiques
class ChartManager {
    static displayChart(chartId, chartData) {
        try {
            const data = JSON.parse(chartData);
            Plotly.newPlot(chartId, data.data, data.layout, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToAdd: ['drawline', 'drawopenpath', 'eraseshape'],
                displaylogo: false
            });
        } catch (error) {
            console.error('Chart error:', error);
            document.getElementById(chartId).innerHTML = `
                <div class="alert alert-danger">
                    Erreur de chargement du graphique
                </div>
            `;
        }
    }
    
    static updateChartPeriod(ticker, period) {
        appState.currentPeriod = period;
        window.location.href = `/analyse?ticker=${ticker}&period=${period}`;
    }
}

// Utilitaires
class Utils {
    static formatNumber(num, decimals = 2) {
        if (num === null || num === undefined) return 'N/A';
        
        num = parseFloat(num);
        
        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(decimals) + 'B';
        }
        if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(decimals) + 'M';
        }
        if (Math.abs(num) >= 1e3) {
            return (num / 1e3).toFixed(decimals) + 'K';
        }
        return num.toFixed(decimals);
    }
    
    static getColorByValue(value, type = 'change') {
        if (type === 'change') {
            if (value > 0) return 'text-success';
            if (value < 0) return 'text-danger';
            return 'text-muted';
        }
        return '';
    }
    
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Fonctions globales
window.appState = new AppState();

function selectTicker(ticker) {
    document.getElementById('search-input').value = ticker;
    document.querySelector('.search-component').search();
}

function quickAnalyze(ticker) {
    window.location.href = `/analyse?ticker=${ticker}`;
}

function changeChartPeriod(period) {
    const ticker = document.querySelector('[data-ticker]')?.dataset.ticker;
    if (ticker) {
        ChartManager.updateChartPeriod(ticker, period);
    }
}

function highlightSuggestion(index) {
    document.querySelectorAll('.suggestion-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les composants
    new SearchComponent();
    
    // Afficher les graphiques
    if (typeof mainChartData !== 'undefined') {
        ChartManager.displayChart('main-chart', mainChartData);
    }
    
    if (typeof rsiChartData !== 'undefined') {
        ChartManager.displayChart('rsi-chart', rsiChartData);
    }
    
    // Mettre à jour les prix en temps réel
    const tickerElement = document.querySelector('[data-ticker]');
    if (tickerElement) {
        const ticker = tickerElement.dataset.ticker;
        setInterval(() => this.updateLivePrice(ticker), 30000); // Toutes les 30 secondes
    }
    
    // Gestion du dark mode
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });
        
        // Restaurer le mode
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }
});

// Mettre à jour le prix en direct
async function updateLivePrice(ticker) {
    try {
        const quote = await ApiService.getQuote(ticker);
        if (quote && quote.price) {
            const priceElement = document.getElementById('live-price');
            const changeElement = document.getElementById('live-change');
            
            if (priceElement) {
                priceElement.textContent = `$${quote.price.toFixed(2)}`;
            }
            
            if (changeElement) {
                changeElement.textContent = `${quote.changePercent.toFixed(2)}%`;
                changeElement.className = `live-change ${quote.changePercent >= 0 ? 'positive' : 'negative'}`;
            }
        }
    } catch (error) {
        console.error('Live price update failed:', error);
    }
}