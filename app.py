# app.py
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import numpy as np
import json
from datetime import datetime, timedelta
import logging
import os
import time
from functools import wraps

# Import our new multi-source fetcher
from modules.data_fetcher import MultiSourceFetcher

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-2024-technical-analysis')
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes cache

cache = Cache(app)

# Initialize the multi-source fetcher
fetcher = MultiSourceFetcher(use_cache=True)

# Configuration complète
PORTEFEUILLES = {
    "US": {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "GOOGL": "Alphabet Inc. (Google)",
        "AMZN": "Amazon.com Inc.",
        "NVDA": "NVIDIA Corporation",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms Inc.",
        "JPM": "JPMorgan Chase & Co.",
        "V": "Visa Inc.",
        "JNJ": "Johnson & Johnson",
        "UNH": "UnitedHealth Group",
        "XOM": "Exxon Mobil Corporation",
        "WMT": "Walmart Inc.",
        "PG": "Procter & Gamble",
        "HD": "Home Depot"
    },
    "EU": {
        "TTE.PA": "TotalEnergies SE",
        "AI.PA": "Air Liquide SA",
        "AIR.PA": "Airbus SE",
        "BNP.PA": "BNP Paribas SA",
        "MC.PA": "LVMH Moët Hennessy",
        "OR.PA": "L'Oréal SA",
        "SAN.PA": "Sanofi SA",
        "SU.PA": "Schneider Electric",
        "GLE.PA": "Société Générale",
        "VOW3.DE": "Volkswagen AG",
        "SAP.DE": "SAP SE",
        "ASML.AS": "ASML Holding"
    },
    "SECTEURS": {
        "XLE": "Énergie SPDR",
        "XLF": "Finances SPDR",
        "XLV": "Santé SPDR",
        "XLK": "Technologie SPDR",
        "XLY": "Cycliques SPDR",
        "XLP": "Consommation courante SPDR"
    }
}

PERIODS = {
    '1mo': '1 Mois',
    '3mo': '3 Mois',
    '6mo': '6 Mois',
    '1y': '1 An',
    '2y': '2 Ans'
}

# Cache pour stocker les données récentes
data_cache = {}

def retry_operation(max_retries=3, delay=2):
    """Décorateur pour réessayer les opérations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Tentative {attempt + 1} échouée pour {func.__name__}: {str(e)}")
                    time.sleep(delay * (attempt + 1))  # Backoff exponentiel
            return func(*args, **kwargs)  # Dernier essai
        return wrapper
    return decorator

class AdvancedTechnicalAnalyzer:
    """Analyseur technique avancé"""
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calcule le RSI"""
        if len(prices) < period:
            return np.full(len(prices), 50)
        
        prices = np.array(prices)
        deltas = np.diff(prices)
        
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi.tolist()
    
    @staticmethod
    def calculate_moving_average(prices, period):
        """Calcule la moyenne mobile"""
        if len(prices) < period:
            return [None] * len(prices)
        
        prices_array = np.array(prices)
        ma = np.full(len(prices), np.nan)
        
        for i in range(period-1, len(prices)):
            ma[i] = np.mean(prices_array[i-period+1:i+1])
        
        return [float(val) if not np.isnan(val) else None for val in ma]
    
    @staticmethod
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calcule les bandes de Bollinger"""
        if len(prices) < period:
            return {
                'upper': [None] * len(prices),
                'middle': [None] * len(prices),
                'lower': [None] * len(prices)
            }
        
        prices_array = np.array(prices)
        middle_band = AdvancedTechnicalAnalyzer.calculate_moving_average(prices, period)
        
        upper_band = [None] * len(prices)
        lower_band = [None] * len(prices)
        
        for i in range(period-1, len(prices)):
            if middle_band[i] is not None:
                std = np.std(prices_array[i-period+1:i+1])
                upper_band[i] = middle_band[i] + (std_dev * std)
                lower_band[i] = middle_band[i] - (std_dev * std)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
        """Calcule le MACD"""
        if len(prices) < slow_period + signal_period:
            return {
                'macd': [0] * len(prices),
                'signal': [0] * len(prices),
                'histogram': [0] * len(prices)
            }
        
        # Calcul des EMA
        def calculate_ema(data, period):
            ema = np.zeros_like(data, dtype=float)
            multiplier = 2 / (period + 1)
            
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
            
            return ema
        
        prices_array = np.array(prices)
        ema_fast = calculate_ema(prices_array, fast_period)
        ema_slow = calculate_ema(prices_array, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line.tolist(),
            'signal': signal_line.tolist(),
            'histogram': histogram.tolist()
        }

@retry_operation(max_retries=2, delay=1)
def get_stock_data(ticker, period="6mo"):
    """Récupère les données d'une action avec le multi-source fetcher"""
    try:
        logger.info(f"📊 Récupération des données pour {ticker} ({period})...")
        
        # Use the multi-source fetcher
        df = fetcher.get_stock_data(ticker, period=period, interval="1d")
        
        if df is None or (hasattr(df, 'empty') and df.empty):
            raise ValueError(f"Aucune donnée disponible pour {ticker}")
        
        # Get company info
        info = fetcher.get_stock_info(ticker)
        company_name = info.get('name', ticker) if info else ticker
        
        # Get source information for logging
        source_stats = fetcher.get_source_stats()
        active_sources = [name for name, stats in source_stats.items() 
                         if stats.get('available', False) and stats.get('successes', 0) > 0]
        if active_sources:
            logger.info(f"Source utilisée pour {ticker}: {active_sources[:1]}")
        else:
            logger.info(f"Using mock data for {ticker}")
        
        return df, company_name, info
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de {ticker}: {str(e)}")
        raise

@cache.memoize(timeout=300)  # Cache pour 5 minutes
def get_cached_stock_data(ticker, period):
    """Version avec cache des données"""
    return get_stock_data(ticker, period)

@app.route('/')
def home():
    """Page d'accueil"""
    return render_template('index.html', 
                         portefeuilles=PORTEFEUILLES,
                         periods=PERIODS)

@app.route('/analyse')
def analyse():
    """Page d'analyse technique"""
    ticker = request.args.get('ticker', '').upper().strip()
    period = request.args.get('period', '6mo')
    
    if not ticker:
        return render_template('analyse.html',
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)
    
    try:
        logger.info(f"📊 Analyse de {ticker} ({period})...")
        
        # Vérifier le cache
        cache_key = f"{ticker}_{period}"
        if cache_key in data_cache:
            cached_time, cached_data = data_cache[cache_key]
            # Si les données ont moins de 5 minutes, les utiliser
            if (datetime.now() - cached_time).total_seconds() < 300:
                logger.info(f"Utilisation des données en cache pour {ticker}")
                stats, chart_data, signals, indicators = cached_data
                return render_template('analyse.html',
                                     stats=stats,
                                     signals=signals,
                                     chart_data=chart_data,
                                     indicators=indicators,
                                     ticker=ticker,
                                     period=period,
                                     portefeuilles=PORTEFEUILLES,
                                     periods=PERIODS)
        
        # Récupérer les données avec le multi-source fetcher
        df, company_name, info = get_cached_stock_data(ticker, period)
        
        # Extraire les données
        dates = df.index.strftime('%Y-%m-%d').tolist()
        closes = df['Close'].tolist()
        opens = df['Open'].tolist()
        highs = df['High'].tolist()
        lows = df['Low'].tolist()
        volumes = df['Volume'].tolist()
        
        # Calculer les indicateurs
        analyzer = AdvancedTechnicalAnalyzer()
        
        # RSI
        rsi_values = analyzer.calculate_rsi(closes)
        
        # Moyennes mobiles
        ma20_values = analyzer.calculate_moving_average(closes, 20)
        ma50_values = analyzer.calculate_moving_average(closes, 50)
        ma200_values = analyzer.calculate_moving_average(closes, 200)
        
        # Bandes de Bollinger
        bollinger_bands = analyzer.calculate_bollinger_bands(closes)
        
        # MACD
        macd_data = analyzer.calculate_macd(closes)
        
        # Volatilité
        if len(closes) > 1:
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 0 else 0
        else:
            volatility = 0
        
        # Signaux d'achat/vente
        signals = []
        if rsi_values:
            current_rsi = rsi_values[-1]
            if current_rsi > 70:
                signals.append(('RSI Surachat', 'danger', current_rsi, 
                              f'RSI à {current_rsi:.1f} > 70 - Signal de vente'))
            elif current_rsi < 30:
                signals.append(('RSI Sous-vente', 'success', current_rsi, 
                              f'RSI à {current_rsi:.1f} < 30 - Signal d\'achat'))
        
        # Signaux de tendance avec moyennes mobiles
        if ma20_values[-1] is not None and ma50_values[-1] is not None:
            if ma20_values[-1] > ma50_values[-1]:
                signals.append(('Tendance Haussière', 'success', None,
                              'MA20 > MA50 - Tendance à la hausse'))
            else:
                signals.append(('Tendance Baissière', 'warning', None,
                              'MA20 < MA50 - Tendance à la baisse'))
        
        # Signaux MACD
        if len(macd_data['macd']) > 1:
            current_macd = macd_data['macd'][-1]
            current_signal = macd_data['signal'][-1]
            prev_macd = macd_data['macd'][-2]
            prev_signal = macd_data['signal'][-2]
            
            if prev_macd < prev_signal and current_macd > current_signal:
                signals.append(('Signal MACD', 'success', current_macd,
                              'MACD croise au-dessus de la ligne de signal - Achat'))
            elif prev_macd > prev_signal and current_macd < current_signal:
                signals.append(('Signal MACD', 'danger', current_macd,
                              'MACD croise en-dessous de la ligne de signal - Vente'))
        
        # Préparer les données pour le graphique
        chart_data = []
        for i in range(len(dates)):
            chart_point = {
                'date': dates[i],
                'open': float(opens[i]),
                'high': float(highs[i]),
                'low': float(lows[i]),
                'close': float(closes[i]),
                'volume': int(volumes[i]),
                'rsi': float(rsi_values[i]) if i < len(rsi_values) else None,
                'ma20': ma20_values[i],
                'ma50': ma50_values[i],
                'ma200': ma200_values[i],
                'bb_upper': bollinger_bands['upper'][i],
                'bb_middle': bollinger_bands['middle'][i],
                'bb_lower': bollinger_bands['lower'][i]
            }
            chart_data.append(chart_point)
        
        # Données supplémentaires pour les indicateurs
        indicators_data = {
            'macd': {
                'values': macd_data['macd'],
                'signal': macd_data['signal'],
                'histogram': macd_data['histogram']
            },
            'bollinger': bollinger_bands
        }
        
        # Statistiques détaillées
        last_close = closes[-1]
        prev_close = closes[-2] if len(closes) > 1 else last_close
        change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close != 0 else 0
        
        # Info de base de l'action
        basic_info = {
            'symbol': info.get('symbol', ticker) if info else ticker,
            'name': company_name,
            'sector': info.get('sector', 'N/A') if info else 'N/A',
            'currency': info.get('currency', 'USD') if info else 'USD',
            'marketCap': info.get('marketCap', 0) if info else 0,
            'peRatio': info.get('peRatio', 0) if info else 0,
            'dividendYield': info.get('dividendYield', 0) if info else 0
        }
        
        stats = {
            'ticker': ticker,
            'company': company_name,
            'last_price': round(last_close, 2),
            'last_date': dates[-1],
            'change_1d': round(change_pct, 2),
            'volume': int(volumes[-1]),
            'avg_volume': int(np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]),
            'rsi': round(rsi_values[-1], 1) if rsi_values else None,
            'ma_20': round(ma20_values[-1], 2) if ma20_values[-1] is not None else None,
            'ma_50': round(ma50_values[-1], 2) if ma50_values[-1] is not None else None,
            'ma_200': round(ma200_values[-1], 2) if ma200_values[-1] is not None else None,
            'volatility': round(volatility, 1),
            'data_points': len(closes),
            'high_52w': info.get('fiftyTwoWeekHigh', max(highs) if highs else 0) if info else max(highs) if highs else 0,
            'low_52w': info.get('fiftyTwoWeekLow', min(lows) if lows else 0) if info else min(lows) if lows else 0,
            'beta': info.get('beta', 0) if info else 0,
            'basic_info': basic_info
        }
        
        # Mettre en cache
        data_cache[cache_key] = (datetime.now(), (stats, chart_data, signals, indicators_data))
        
        logger.info(f"✅ Analyse terminée: {ticker} - {len(chart_data)} points de données")
        
        return render_template('analyse.html',
                             stats=stats,
                             signals=signals,
                             chart_data=chart_data,
                             indicators=indicators_data,
                             ticker=ticker,
                             period=period,
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse de {ticker}: {str(e)}")
        
        # Message d'erreur convivial
        error_message = f"Impossible d'analyser {ticker}. "
        
        # Vérifier les sources disponibles
        source_stats = fetcher.get_source_stats()
        available_sources = [name for name, stats in source_stats.items() 
                           if stats.get('available', False) and stats.get('successes', 0) > 0]
        
        if not available_sources:
            error_message += "Toutes les sources de données sont temporairement indisponibles. "
            error_message += "Utilisation des données simulées pour la démonstration."
            
            # Try to show mock data as fallback
            try:
                # Create simple mock data for demonstration
                stats = {
                    'ticker': ticker,
                    'company': f"{ticker} Corporation",
                    'last_price': 100.0,
                    'change_1d': 0.0,
                    'volume': 1000000,
                    'rsi': 50.0,
                    'ma_20': 99.5,
                    'ma_50': 98.0,
                    'note': 'Données simulées - Mode démonstration'
                }
                
                return render_template('analyse.html',
                                     stats=stats,
                                     signals=[],
                                     ticker=ticker,
                                     period=period,
                                     portefeuilles=PORTEFEUILLES,
                                     periods=PERIODS,
                                     demo_mode=True)
            except:
                pass
        
        error_message += " Veuillez réessayer dans quelques minutes."
        
        return render_template('analyse.html',
                             error=error_message,
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)

@app.route('/api/search')
def search_tickers():
    """API pour la recherche en temps réel"""
    query = request.args.get('q', '').lower()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    # Use the fetcher's search function
    suggestions = fetcher.search_tickers(query, limit=10)
    
    # Also search in our predefined portfolios
    for market, stocks in PORTEFEUILLES.items():
        for ticker, name in stocks.items():
            if (query in ticker.lower() or query in name.lower()) and \
               len(suggestions) < 10:
                # Check if not already in suggestions
                if not any(s.get('symbol') == ticker for s in suggestions):
                    info = fetcher.get_stock_info(ticker)
                    if info:
                        suggestions.append(info)
                    else:
                        suggestions.append({
                            'symbol': ticker,
                            'name': name,
                            'market': market,
                            'currency': 'EUR' if '.PA' in ticker else 'USD'
                        })
    
    return jsonify({'suggestions': suggestions[:10]})

@app.route('/portefeuille')
def portefeuille():
    """Page des portefeuilles"""
    market = request.args.get('market', 'US')
    stocks = PORTEFEUILLES.get(market, PORTEFEUILLES['US'])
    
    # Get current quotes for all stocks in the portfolio
    portfolio_data = []
    for ticker, name in stocks.items():
        try:
            quote = fetcher.get_quote(ticker)
            if quote:
                portfolio_data.append({
                    'ticker': ticker,
                    'name': name,
                    'price': quote['price'],
                    'change': quote['change'],
                    'changePercent': quote['changePercent'],
                    'volume': quote['volume']
                })
            else:
                portfolio_data.append({
                    'ticker': ticker,
                    'name': name,
                    'price': 0,
                    'change': 0,
                    'changePercent': 0,
                    'volume': 0,
                    'error': 'Données non disponibles'
                })
        except Exception as e:
            logger.warning(f"Erreur pour {ticker}: {e}")
            portfolio_data.append({
                'ticker': ticker,
                'name': name,
                'price': 0,
                'change': 0,
                'changePercent': 0,
                'volume': 0,
                'error': 'Erreur de récupération'
            })
    
    return render_template('portefeuille.html',
                         market=market,
                         portfolio_data=portfolio_data,
                         portefeuilles=PORTEFEUILLES)

@app.route('/dashboard')
def dashboard():
    """Tableau de bord"""
    # Get statistics about data sources
    source_stats = fetcher.get_source_stats()
    
    # Get some popular stocks for the dashboard
    popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    dashboard_data = []
    
    for ticker in popular_stocks:
        try:
            quote = fetcher.get_quote(ticker)
            info = fetcher.get_stock_info(ticker)
            
            if quote and info:
                dashboard_data.append({
                    'ticker': ticker,
                    'name': info.get('name', ticker),
                    'price': quote['price'],
                    'change': quote['change'],
                    'changePercent': quote['changePercent'],
                    'sector': info.get('sector', 'N/A')
                })
        except Exception as e:
            logger.debug(f"Dashboard: Erreur pour {ticker}: {e}")
    
    return render_template('dashboard.html',
                         dashboard_data=dashboard_data,
                         source_stats=source_stats)

@app.route('/api/system/health')
def system_health():
    """API pour vérifier l'état du système"""
    source_stats = fetcher.get_source_stats()
    
    # Check which sources are working
    working_sources = []
    for name, stats in source_stats.items():
        if stats.get('available', False) and stats.get('successes', 0) > 0:
            working_sources.append(name)
    
    health_status = {
        'status': 'healthy' if working_sources else 'degraded',
        'working_sources': working_sources,
        'total_sources': len(source_stats),
        'cache_enabled': True,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(health_status)

@app.route('/api/test/<ticker>')
def test_data_source(ticker):
    """API de test pour les sources de données"""
    try:
        # Test avec le multi-source fetcher
        df = fetcher.get_stock_data(ticker, period="1d", interval="1d")
        info = fetcher.get_stock_info(ticker)
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée disponible',
                'ticker': ticker,
                'sources': fetcher.get_source_stats()
            })
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'last_price': float(df['Close'].iloc[-1]) if not df.empty else 0,
            'data_points': len(df),
            'company_name': info.get('name', ticker) if info else ticker,
            'source': info.get('source', 'unknown') if info else 'unknown',
            'sources_available': fetcher.get_source_stats()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker,
            'sources': fetcher.get_source_stats()
        })

@app.route('/api/system/clear_cache')
def clear_cache():
    """API pour vider le cache"""
    try:
        fetcher.clear_cache()
        data_cache.clear()
        return jsonify({
            'success': True,
            'message': 'Cache vidé avec succès',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    logger.info("🚀 Technical Analyst démarré")
    logger.info(f"📊 NumPy version: {np.__version__}")
    logger.info("🌐 http://localhost:5000")
    logger.info("🔧 Multi-source fetcher initialisé")
    
    # Afficher les statistiques des sources
    source_stats = fetcher.get_source_stats()
    logger.info(f"Sources disponibles: {len([s for s in source_stats.values() if s.get('available')])}/{len(source_stats)}")
    
    # Test de connexion avec la source la plus prioritaire
    try:
        test_quote = fetcher.get_quote("AAPL")
        if test_quote:
            logger.info(f"✅ Test de connexion réussi: AAPL = ${test_quote['price']:.2f}")
            
            # Afficher les sources actives
            active_sources = []
            for name, stats in source_stats.items():
                if stats.get('successes', 0) > 0:
                    active_sources.append(name)
            
            if active_sources:
                logger.info(f"✅ Sources actives: {', '.join(active_sources)}")
            else:
                logger.info("⚠️  Utilisation des données simulées")
        else:
            logger.warning("⚠️  Test de connexion échoué, utilisation du mode démonstration")
    except Exception as e:
        logger.warning(f"⚠️  Erreur de test: {str(e)}")
        logger.info("📱 L'application fonctionnera en mode démonstration avec des données simulées")
    
    app.run(debug=True, host='0.0.0.0', port=5000)