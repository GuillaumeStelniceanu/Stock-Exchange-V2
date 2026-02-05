//static/js/charts.js
/**
 * Module de gestion des graphiques interactifs
 */

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.config = {
            colors: {
                candleUp: '#26a69a',
                candleDown: '#ef5350',
                ma20: '#FF9800',
                ma50: '#2196F3',
                ma200: '#9C27B0',
                volumeUp: 'rgba(38, 166, 154, 0.7)',
                volumeDown: 'rgba(239, 83, 80, 0.7)',
                rsi: '#FFEB3B',
                macd: '#00BCD4',
                macdSignal: '#E91E63',
                bbUpper: '#757575',
                bbLower: '#757575'
            },
            layout: {
                template: 'plotly_dark',
                hovermode: 'x unified',
                showlegend: true,
                legend: {
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "right",
                    x: 1
                },
                xaxis: {
                    rangeslider: { visible: false },
                    type: 'date'
                },
                yaxis: {
                    fixedrange: false,
                    autorange: true
                }
            }
        };
    }

    /**
     * Crée un graphique candlestick avec indicateurs
     */
    createMainChart(containerId, data, ticker, companyName) {
        try {
            if (!data || data.length === 0) {
                throw new Error('Données manquantes');
            }

            // Préparer les données
            const dates = data.map(d => d.date);
            const opens = data.map(d => d.open);
            const highs = data.map(d => d.high);
            const lows = data.map(d => d.low);
            const closes = data.map(d => d.close);
            const volumes = data.map(d => d.volume);

            // Créer les traces
            const traces = [];

            // 1. Candlesticks
            traces.push({
                type: 'candlestick',
                x: dates,
                open: opens,
                high: highs,
                low: lows,
                close: closes,
                name: 'OHLC',
                increasing: { line: { color: this.config.colors.candleUp } },
                decreasing: { line: { color: this.config.colors.candleDown } },
                yaxis: 'y'
            });

            // 2. Moyennes mobiles (si disponibles)
            if (data[0].ma20 !== undefined) {
                traces.push({
                    type: 'scatter',
                    x: dates,
                    y: data.map(d => d.ma20),
                    name: 'MA20',
                    line: { color: this.config.colors.ma20, width: 1.5 },
                    opacity: 0.7,
                    yaxis: 'y'
                });
            }

            if (data[0].ma50 !== undefined) {
                traces.push({
                    type: 'scatter',
                    x: dates,
                    y: data.map(d => d.ma50),
                    name: 'MA50',
                    line: { color: this.config.colors.ma50, width: 1.5 },
                    opacity: 0.7,
                    yaxis: 'y'
                });
            }

            if (data[0].ma200 !== undefined) {
                traces.push({
                    type: 'scatter',
                    x: dates,
                    y: data.map(d => d.ma200),
                    name: 'MA200',
                    line: { color: this.config.colors.ma200, width: 1.5 },
                    opacity: 0.7,
                    yaxis: 'y'
                });
            }

            // 3. Bandes de Bollinger (si disponibles)
            if (data[0].bbUpper !== undefined && data[0].bbLower !== undefined) {
                traces.push({
                    type: 'scatter',
                    x: dates,
                    y: data.map(d => d.bbUpper),
                    name: 'BB Upper',
                    line: { color: this.config.colors.bbUpper, width: 1, dash: 'dash' },
                    opacity: 0.5,
                    showlegend: false,
                    yaxis: 'y'
                });

                traces.push({
                    type: 'scatter',
                    x: dates,
                    y: data.map(d => d.bbLower),
                    name: 'BB Lower',
                    line: { color: this.config.colors.bbLower, width: 1, dash: 'dash' },
                    opacity: 0.5,
                    fill: 'tonexty',
                    fillcolor: 'rgba(128, 128, 128, 0.1)',
                    showlegend: false,
                    yaxis: 'y'
                });
            }

            // 4. Volume
            const volumeColors = closes.map((close, i) => 
                close >= opens[i] ? this.config.colors.volumeUp : this.config.colors.volumeDown
            );

            traces.push({
                type: 'bar',
                x: dates,
                y: volumes,
                name: 'Volume',
                marker: { color: volumeColors },
                opacity: 0.7,
                yaxis: 'y2'
            });

            // Configuration du layout
            const layout = {
                ...this.config.layout,
                title: `${companyName} (${ticker})`,
                height: 600,
                grid: {
                    rows: 2,
                    columns: 1,
                    pattern: 'independent',
                    roworder: 'top to bottom'
                },
                yaxis: {
                    title: 'Prix',
                    domain: [0.3, 1]
                },
                yaxis2: {
                    title: 'Volume',
                    domain: [0, 0.25],
                    showgrid: false
                }
            };

            // Configuration
            const config = {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToAdd: [
                    'drawline',
                    'drawopenpath',
                    'drawclosedpath',
                    'drawcircle',
                    'drawrect',
                    'eraseshape'
                ],
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                displaylogo: false,
                toImageButtonOptions: {
                    format: 'png',
                    filename: `chart_${ticker}_${new Date().toISOString().split('T')[0]}`,
                    height: 800,
                    width: 1200,
                    scale: 2
                }
            };

            // Créer le graphique
            const chart = Plotly.newPlot(containerId, traces, layout, config);
            
            // Sauvegarder la référence
            this.charts.set(containerId, chart);

            // Ajouter les événements
            this.addChartEvents(containerId);

            return chart;

        } catch (error) {
            console.error('Erreur création graphique:', error);
            document.getElementById(containerId).innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Erreur lors du chargement du graphique: ${error.message}
                </div>
            `;
            return null;
        }
    }

    /**
     * Crée un graphique RSI
     */
    createRSIChart(containerId, data) {
        try {
            if (!data || data.length === 0 || data[0].rsi === undefined) {
                return null;
            }

            const dates = data.map(d => d.date);
            const rsiValues = data.map(d => d.rsi);

            const trace = {
                type: 'scatter',
                x: dates,
                y: rsiValues,
                name: 'RSI (14)',
                line: { color: this.config.colors.rsi, width: 2 }
            };

            const layout = {
                ...this.config.layout,
                title: 'RSI - Relative Strength Index',
                height: 300,
                yaxis: {
                    range: [0, 100],
                    zeroline: false
                },
                shapes: [
                    // Zone de surachat
                    {
                        type: 'rect',
                        xref: 'paper',
                        yref: 'y',
                        x0: 0,
                        x1: 1,
                        y0: 70,
                        y1: 100,
                        fillcolor: 'rgba(255, 0, 0, 0.1)',
                        line: { width: 0 }
                    },
                    // Zone de survente
                    {
                        type: 'rect',
                        xref: 'paper',
                        yref: 'y',
                        x0: 0,
                        x1: 1,
                        y0: 0,
                        y1: 30,
                        fillcolor: 'rgba(0, 255, 0, 0.1)',
                        line: { width: 0 }
                    }
                ],
                annotations: [
                    {
                        x: dates[0],
                        y: 70,
                        text: 'SURACHAT',
                        showarrow: false,
                        font: { color: 'red', size: 10 },
                        xanchor: 'left'
                    },
                    {
                        x: dates[0],
                        y: 30,
                        text: 'SURVENTE',
                        showarrow: false,
                        font: { color: 'green', size: 10 },
                        xanchor: 'left'
                    }
                ]
            };

            const config = {
                responsive: true,
                displayModeBar: false
            };

            const chart = Plotly.newPlot(containerId, [trace], layout, config);
            this.charts.set(containerId, chart);

            return chart;

        } catch (error) {
            console.error('Erreur création RSI:', error);
            return null;
        }
    }

    /**
     * Crée un graphique MACD
     */
    createMACDChart(containerId, data) {
        try {
            if (!data || data.length === 0 || 
                data[0].macd === undefined || data[0].macdSignal === undefined) {
                return null;
            }

            const dates = data.map(d => d.date);
            const macdValues = data.map(d => d.macd);
            const signalValues = data.map(d => d.macdSignal);
            const histogramValues = data.map(d => d.macdHist);

            const traces = [
                {
                    type: 'scatter',
                    x: dates,
                    y: macdValues,
                    name: 'MACD',
                    line: { color: this.config.colors.macd, width: 2 }
                },
                {
                    type: 'scatter',
                    x: dates,
                    y: signalValues,
                    name: 'Signal',
                    line: { color: this.config.colors.macdSignal, width: 1.5 }
                },
                {
                    type: 'bar',
                    x: dates,
                    y: histogramValues,
                    name: 'Histogram',
                    marker: {
                        color: histogramValues.map(val => val >= 0 ? 
                            this.config.colors.candleUp : this.config.colors.candleDown)
                    },
                    opacity: 0.5
                }
            ];

            const layout = {
                ...this.config.layout,
                title: 'MACD - Moving Average Convergence Divergence',
                height: 300,
                yaxis: { zeroline: true, zerolinecolor: 'gray' }
            };

            const config = {
                responsive: true,
                displayModeBar: false
            };

            const chart = Plotly.newPlot(containerId, traces, layout, config);
            this.charts.set(containerId, chart);

            return chart;

        } catch (error) {
            console.error('Erreur création MACD:', error);
            return null;
        }
    }

    /**
     * Met à jour un graphique existant
     */
    updateChart(containerId, data) {
        try {
            const chart = this.charts.get(containerId);
            if (!chart) {
                console.warn(`Graphique ${containerId} non trouvé`);
                return;
            }

            // Mettre à jour les données
            const update = {
                'x': [data.map(d => d.date)],
                'y': [data.map(d => d.close)]
            };

            Plotly.react(containerId, update);

        } catch (error) {
            console.error('Erreur mise à jour graphique:', error);
        }
    }

    /**
     * Ajoute des événements au graphique
     */
    addChartEvents(containerId) {
        const element = document.getElementById(containerId);
        if (!element) return;

        // Zoom avec molette
        element.on('plotly_wheel', (event) => {
            event.preventDefault();
            
            if (event.deltaY > 0) {
                // Zoom out
                Plotly.relayout(containerId, {
                    'xaxis.range[0]': event.xaxis.range[0] * 1.2,
                    'xaxis.range[1]': event.xaxis.range[1] * 0.8
                });
            } else {
                // Zoom in
                Plotly.relayout(containerId, {
                    'xaxis.range[0]': event.xaxis.range[0] * 0.8,
                    'xaxis.range[1]': event.xaxis.range[1] * 1.2
                });
            }
        });

        // Double-clic pour réinitialiser le zoom
        element.on('plotly_doubleclick', () => {
            Plotly.relayout(containerId, {
                'xaxis.autorange': true,
                'yaxis.autorange': true
            });
        });

        // Clic droit pour menu contextuel
        element.on('plotly_click', (data) => {
            if (data.event.button === 2) { // Clic droit
                this.showChartContextMenu(data.event, data.points[0]);
            }
        });
    }

    /**
     * Affiche un menu contextuel pour le graphique
     */
    showChartContextMenu(event, point) {
        event.preventDefault();

        // Créer le menu
        const menu = document.createElement('div');
        menu.className = 'chart-context-menu';
        menu.style.cssText = `
            position: fixed;
            top: ${event.clientY}px;
            left: ${event.clientX}px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
            min-width: 200px;
        `;

        const date = new Date(point.x).toLocaleDateString();
        const price = point.y.toFixed(2);

        menu.innerHTML = `
            <div class="menu-header p-2 border-bottom">
                <small class="text-muted">${date}</small>
                <div class="fw-bold">$${price}</div>
            </div>
            <div class="menu-actions">
                <button class="menu-item" onclick="chartManager.addHorizontalLine(${point.y})">
                    <i class="fas fa-arrows-alt-h me-2"></i>Ajouter ligne horizontale
                </button>
                <button class="menu-item" onclick="chartManager.addVerticalLine('${point.x}')">
                    <i class="fas fa-arrows-alt-v me-2"></i>Ajouter ligne verticale
                </button>
                <button class="menu-item" onclick="chartManager.addAnnotation('${point.x}', ${point.y})">
                    <i class="fas fa-sticky-note me-2"></i>Ajouter annotation
                </button>
                <hr class="my-1">
                <button class="menu-item" onclick="chartManager.exportChartData()">
                    <i class="fas fa-download me-2"></i>Exporter les données
                </button>
                <button class="menu-item" onclick="chartManager.takeScreenshot()">
                    <i class="fas fa-camera me-2"></i>Prendre une capture
                </button>
            </div>
        `;

        // Styles pour les éléments du menu
        const style = document.createElement('style');
        style.textContent = `
            .menu-item {
                display: block;
                width: 100%;
                padding: 8px 12px;
                text-align: left;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }
            .menu-item:hover {
                background-color: #f8f9fa;
            }
        `;
        document.head.appendChild(style);

        document.body.appendChild(menu);

        // Fermer le menu en cliquant ailleurs
        const closeMenu = (e) => {
            if (!menu.contains(e.target)) {
                document.body.removeChild(menu);
                document.head.removeChild(style);
                document.removeEventListener('click', closeMenu);
            }
        };

        setTimeout(() => {
            document.addEventListener('click', closeMenu);
        }, 100);
    }

    /**
     * Ajoute une ligne horizontale au graphique
     */
    addHorizontalLine(price, containerId = 'main-chart') {
        const chart = this.charts.get(containerId);
        if (!chart) return;

        const layoutUpdate = {
            shapes: [{
                type: 'line',
                x0: 0,
                x1: 1,
                y0: price,
                y1: price,
                xref: 'paper',
                yref: 'y',
                line: {
                    color: 'yellow',
                    width: 2,
                    dash: 'dash'
                }
            }]
        };

        Plotly.relayout(containerId, layoutUpdate);
    }

    /**
     * Ajoute une ligne verticale au graphique
     */
    addVerticalLine(date, containerId = 'main-chart') {
        const chart = this.charts.get(containerId);
        if (!chart) return;

        const layoutUpdate = {
            shapes: [{
                type: 'line',
                x0: date,
                x1: date,
                y0: 0,
                y1: 1,
                xref: 'x',
                yref: 'paper',
                line: {
                    color: 'cyan',
                    width: 2,
                    dash: 'dash'
                }
            }]
        };

        Plotly.relayout(containerId, layoutUpdate);
    }

    /**
     * Exporte les données du graphique
     */
    exportChartData(containerId = 'main-chart') {
        const chart = this.charts.get(containerId);
        if (!chart) return;

        Plotly.downloadImage(containerId, {
            format: 'png',
            filename: `chart_export_${new Date().toISOString()}`,
            height: 800,
            width: 1200,
            scale: 2
        });
    }

    /**
     * Prend une capture d'écran du graphique
     */
    takeScreenshot(containerId = 'main-chart') {
        const element = document.getElementById(containerId);
        if (!element) return;

        html2canvas(element).then(canvas => {
            const link = document.createElement('a');
            link.download = `screenshot_${new Date().toISOString()}.png`;
            link.href = canvas.toDataURL();
            link.click();
        });
    }

    /**
     * Redimensionne tous les graphiques
     */
    resizeCharts() {
        this.charts.forEach((chart, containerId) => {
            Plotly.Plots.resize(document.getElementById(containerId));
        });
    }

    /**
     * Nettoie tous les graphiques
     */
    cleanup() {
        this.charts.forEach((chart, containerId) => {
            Plotly.purge(containerId);
        });
        this.charts.clear();
    }
}

// Exporter une instance globale
window.chartManager = new ChartManager();

// Redimensionner les graphiques lors du redimensionnement de la fenêtre
window.addEventListener('resize', () => {
    if (window.chartManager) {
        window.chartManager.resizeCharts();
    }
});

// Exporter les fonctions utilitaires
window.ChartUtils = {
    formatNumber: (num, decimals = 2) => {
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
    },

    formatDate: (date, format = 'short') => {
        const d = new Date(date);
        
        if (format === 'short') {
            return d.toLocaleDateString();
        } else if (format === 'long') {
            return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
        } else if (format === 'chart') {
            return d.toLocaleDateString('fr-FR', { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
        
        return d.toISOString();
    },

    generateColorScale: (values) => {
        const min = Math.min(...values);
        const max = Math.max(...values);
        
        return values.map(value => {
            const ratio = (value - min) / (max - min);
            
            // De rouge (bas) à vert (haut)
            const r = Math.floor(255 * (1 - ratio));
            const g = Math.floor(255 * ratio);
            const b = 0;
            
            return `rgb(${r}, ${g}, ${b})`;
        });
    }
};