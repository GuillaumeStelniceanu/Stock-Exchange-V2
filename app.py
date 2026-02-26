# app.py - OPTIMIZED WITH REAL-TIME DATA & FAST CACHING
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache
import json
import numpy as np
from datetime import datetime
import logging
import os
import json

# Import optimized modules
from modules.data_fetcher import default_fetcher as fetcher

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-2024')
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 180  # 3 minutes for faster updates

cache = Cache(app)

# EXPANDED STOCK LIST
PORTEFEUILLES = {
    "US": {
        "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.", "NVDA": "NVIDIA Corp.", "TSLA": "Tesla Inc.",
        "META": "Meta Platforms Inc.", "JPM": "JPMorgan Chase", "V": "Visa Inc.",
        "JNJ": "Johnson & Johnson", "WMT": "Walmart Inc.", "PG": "Procter & Gamble",
        "UNH": "UnitedHealth Group", "MA": "Mastercard", "HD": "Home Depot",
        "BAC": "Bank of America", "DIS": "Walt Disney", "NFLX": "Netflix",
        "ADBE": "Adobe Inc.", "CSCO": "Cisco Systems", "PFE": "Pfizer",
        "KO": "Coca-Cola", "INTC": "Intel Corp.", "AMD": "AMD Inc.",
        "XOM": "Exxon Mobil", "CVX": "Chevron", "MRK": "Merck & Co."
    },
    "EU": {
        "TTE.PA": "TotalEnergies SE", "AI.PA": "Air Liquide SA",
        "AIR.PA": "Airbus SE", "BNP.PA": "BNP Paribas SA", "MC.PA": "LVMH",
        "OR.PA": "L'Oréal", "SAN.PA": "Sanofi", "SU.PA": "Schneider Electric",
        "GLE.PA": "Société Générale", "SAP.DE": "SAP SE", "VOW3.DE": "Volkswagen",
        "ASML.AS": "ASML Holding", "HSBA.L": "HSBC Holdings", "BP.L": "BP plc",
        "ULVR.L": "Unilever", "AZN.L": "AstraZeneca", "SHEL.L": "Shell plc",
        "DTE.DE": "Deutsche Telekom", "SIE.DE": "Siemens", "ALV.DE": "Allianz"
    }
}

PERIODS = {
    '1mo': '1 Mois', '3mo': '3 Mois', '6mo': '6 Mois',
    '1y': '1 An', '2y': '2 Ans'
}

# Utility functions
def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def calculate_rsi(prices, period=14):
    """Fast RSI calculation"""
    if len(prices) < period + 1:
        return None
    prices = np.array(prices)
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gain[:period])
    avg_loss = np.mean(loss[:period])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))

def calculate_ma(prices, period):
    """Fast MA calculation"""
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))

def calculate_volatility(prices):
    """Calculate volatility"""
    if len(prices) < 2:
        return 0
    returns = np.diff(prices) / prices[:-1]
    return float(np.std(returns) * np.sqrt(252) * 100)  # Annualized

# Routes
@app.route('/')
def home():
    """Homepage"""
    return render_template('index.html',
                         portefeuilles=PORTEFEUILLES,
                         periods=PERIODS)

@app.route('/analyse')
@cache.cached(timeout=180, query_string=True)
def analyse():
    """Analysis page with FIXED CHARTS"""
    ticker = request.args.get('ticker', '').upper().strip()
    period = request.args.get('period', '6mo')

    if not ticker:
        return render_template('analyse.html',
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)

    try:
        logger.info(f"Analyzing {ticker} ({period})")

        # Get data
        df = fetcher.get_stock_data(ticker, period=period, interval="1d")

        if df is None or df.empty:
            raise ValueError(f"No data for {ticker}")

        info = fetcher.get_stock_info(ticker)
        current_price = safe_float(df['Close'].iloc[-1])
        prev_price = safe_float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
        price_change = current_price - prev_price
        price_change_percent = (price_change / prev_price * 100) if prev_price > 0 else 0

        closes = [safe_float(x) for x in df['Close'].tolist()]
        opens = [safe_float(x) for x in df['Open'].tolist()]
        highs = [safe_float(x) for x in df['High'].tolist()]
        lows = [safe_float(x) for x in df['Low'].tolist()]
        volumes = [int(x) for x in df['Volume'].tolist()]
        dates = [str(d.date()) if hasattr(d, 'date') else str(d)[:10] for d in df.index.tolist()]

        # Moving averages
        ma20 = [None] * len(closes)
        ma50 = [None] * len(closes)
        ma200 = [None] * len(closes)
        for i in range(len(closes)):
            if i >= 19:
                ma20[i] = round(float(np.mean(closes[max(0, i-19):i+1])), 2)
            if i >= 49:
                ma50[i] = round(float(np.mean(closes[max(0, i-49):i+1])), 2)
            if i >= 199:
                ma200[i] = round(float(np.mean(closes[max(0, i-199):i+1])), 2)

        # Bollinger Bands
        bb_upper = [None] * len(closes)
        bb_lower = [None] * len(closes)
        bb_mid = [None] * len(closes)
        for i in range(19, len(closes)):
            window = closes[i-19:i+1]
            m = float(np.mean(window))
            s = float(np.std(window))
            bb_mid[i] = round(m, 2)
            bb_upper[i] = round(m + 2 * s, 2)
            bb_lower[i] = round(m - 2 * s, 2)

        # VWAP
        vwap = [None] * len(closes)
        cum_pv = 0
        cum_v = 0
        for i in range(len(closes)):
            typ = (highs[i] + lows[i] + closes[i]) / 3
            cum_pv += typ * volumes[i]
            cum_v += volumes[i]
            vwap[i] = round(cum_pv / cum_v, 2) if cum_v > 0 else None

        # RSI series (Wilder smoothing)
        closes_arr = np.array(closes)
        n = len(closes_arr)
        rsi_series = [None] * n
        if n > 15:
            deltas = np.diff(closes_arr)
            gains = np.where(deltas > 0, deltas, 0.0)
            losses = np.where(deltas < 0, -deltas, 0.0)
            avg_gain = float(np.mean(gains[:14]))
            avg_loss = float(np.mean(losses[:14]))
            for i in range(14, n - 1):
                avg_gain = (avg_gain * 13 + gains[i]) / 14
                avg_loss = (avg_loss * 13 + losses[i]) / 14
                rs = avg_gain / avg_loss if avg_loss != 0 else 0
                rsi_series[i + 1] = round(100 - (100 / (1 + rs)), 2)

        # EMA helper
        def ewm_series(arr, span):
            result = [None] * len(arr)
            alpha = 2.0 / (span + 1)
            last = None
            for i, v in enumerate(arr):
                if v is None:
                    continue
                if last is None:
                    last = v
                else:
                    last = alpha * v + (1 - alpha) * last
                result[i] = round(last, 6)
            return result

        # MACD (12, 26, 9)
        ema12 = ewm_series(closes, 12)
        ema26 = ewm_series(closes, 26)
        macd_line = [round(ema12[i] - ema26[i], 6) if (ema12[i] is not None and ema26[i] is not None) else None for i in range(n)]
        macd_signal_raw = [None] * n
        alpha9 = 2.0 / 10
        last = None
        for i in range(n):
            if macd_line[i] is not None:
                if last is None:
                    last = macd_line[i]
                else:
                    last = alpha9 * macd_line[i] + (1 - alpha9) * last
                macd_signal_raw[i] = round(last, 6)
        macd_hist = [round(macd_line[i] - macd_signal_raw[i], 6)
                     if (macd_line[i] is not None and macd_signal_raw[i] is not None) else None
                     for i in range(n)]

        chart_data = json.dumps({
            'dates': dates, 'close': closes, 'open': opens,
            'high': highs, 'low': lows, 'volume': volumes,
            'ma20': ma20, 'ma50': ma50, 'ma200': ma200,
            'bb_upper': bb_upper, 'bb_lower': bb_lower,
            'vwap': vwap,
            'rsi': rsi_series,
            'macd': macd_line, 'macd_signal': macd_signal_raw, 'macd_hist': macd_hist
        })

        # Technical analysis
        rsi = calculate_rsi(closes)
        ma20_val = calculate_ma(closes, 20)
        ma50_val = calculate_ma(closes, 50)
        volatility = calculate_volatility(closes)

        signals = []
        if rsi:
            if rsi < 30:
                signals.append({'type': 'BUY', 'indicator': 'RSI', 'message': f'RSI survendu ({rsi:.1f})'})
            elif rsi > 70:
                signals.append({'type': 'SELL', 'indicator': 'RSI', 'message': f'RSI suracheté ({rsi:.1f})'})
        if ma20_val and ma50_val:
            if current_price > ma20_val > ma50_val:
                signals.append({'type': 'BUY', 'indicator': 'MA', 'message': 'Prix au-dessus des MMs'})
            elif current_price < ma20_val < ma50_val:
                signals.append({'type': 'SELL', 'indicator': 'MA', 'message': 'Prix en-dessous des MMs'})

        buy_signals = sum(1 for s in signals if s['type'] == 'BUY')
        sell_signals = sum(1 for s in signals if s['type'] == 'SELL')
        if buy_signals > sell_signals:
            overall = 'BUY'
        elif sell_signals > buy_signals:
            overall = 'SELL'
        else:
            overall = 'NEUTRAL'

        analysis = {
            'rsi': round(rsi, 2) if rsi else None,
            'ma20': round(ma20_val, 2) if ma20_val else None,
            'ma50': round(ma50_val, 2) if ma50_val else None,
            'volatility': round(volatility, 2),
            'signals': signals,
            'overall': overall,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals
        }

        company_name = info.get('name', ticker) if info else ticker

        historical_data = []
        for i in range(len(dates)):
            change = ((closes[i] - closes[i-1]) / closes[i-1] * 100) if i > 0 else 0
            historical_data.append({
                'date': dates[i], 'open': opens[i], 'high': highs[i],
                'low': lows[i], 'close': closes[i], 'volume': volumes[i],
                'change': change
            })

        stock_info = {
            'name': company_name,
            'sector': info.get('sector', 'N/A') if info else 'N/A',
            'fiftyTwoWeekHigh': safe_float(info.get('fiftyTwoWeekHigh', 0) if info else 0),
            'fiftyTwoWeekLow': safe_float(info.get('fiftyTwoWeekLow', 0) if info else 0),
            'beta': safe_float(info.get('beta', 0) if info else 0),
            'peRatio': safe_float(info.get('peRatio', 0) if info else 0),
            'dividendYield': safe_float(info.get('dividendYield', 0) if info else 0),
            'marketCap': safe_float(info.get('marketCap', 0) if info else 0)
        }

        logger.info(f"✓ Analysis complete: {ticker}")

        return render_template('analyse.html',
                             ticker=ticker,
                             period=period,
                             current_price=round(current_price, 2),
                             price_change=round(price_change, 2),
                             price_change_percent=round(price_change_percent, 2),
                             current_volume=int(volumes[-1]) if volumes else 0,
                             analysis=analysis,
                             stock_info=stock_info,
                             chart_data=chart_data,
                             historical_data=historical_data,
                             period_label=PERIODS.get(period, '6 Mois'),
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return render_template('analyse.html',
                             error=f"Impossible d'analyser {ticker}. Veuillez réessayer.",
                             ticker=ticker,
                             period=period,
                             portefeuilles=PORTEFEUILLES,
                             periods=PERIODS)

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    popular = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    stocks_data = []

    for ticker in popular:
        try:
            quote = fetcher.get_quote(ticker)
            info = fetcher.get_stock_info(ticker)
            stocks_data.append({
                'ticker': ticker,
                'name': info.get('name', ticker) if info else ticker,
                'price': safe_float(quote.get('price')),
                'change': safe_float(quote.get('change')),
                'change_percent': safe_float(quote.get('changePercent')),
                'sector': info.get('sector', 'N/A') if info else 'N/A'
            })
        except Exception as e:
            logger.debug(f"Dashboard error for {ticker}: {e}")

    return render_template('dashboard.html',
                         stats={
                             'active_sources': 2,
                             'cached_items': 50,
                             'tracked_stocks': len(stocks_data),
                             'last_update': "À l'instant"
                         },
                         portefeuilles=PORTEFEUILLES)

@app.route('/portefeuille')
def portefeuille():
    """Portfolio page with REAL-TIME data"""
    try:
        market = request.args.get('market', 'US')
        stocks = PORTEFEUILLES.get(market, PORTEFEUILLES['US'])

        portfolio_data = []
        positive_count = 0
        negative_count = 0

        for ticker, name in stocks.items():
            try:
                quote = fetcher.get_quote(ticker)
                price = safe_float(quote.get('price'))
                change = safe_float(quote.get('change'))
                change_pct = safe_float(quote.get('changePercent'))

                if change >= 0:
                    positive_count += 1
                else:
                    negative_count += 1

                portfolio_data.append({
                    'ticker': ticker,
                    'name': name,
                    'price': price,
                    'change': change,
                    'change_percent': change_pct,
                    'error': None
                })
            except Exception as e:
                portfolio_data.append({
                    'ticker': ticker,
                    'name': name,
                    'price': None,
                    'change': None,
                    'change_percent': None,
                    'error': str(e)
                })

        return render_template('portefeuille.html',
                             portfolio_data=portfolio_data,
                             market=market,
                             positive_count=positive_count,
                             negative_count=negative_count,
                             portefeuilles=PORTEFEUILLES,
                             current_year=datetime.now().year)

    except Exception as e:
        logger.error(f"Portfolio error: {e}")
        return render_template('portefeuille.html',
                             portfolio_data=[],
                             market='US',
                             positive_count=0,
                             negative_count=0,
                             error="Impossible de charger le portefeuille",
                             portefeuilles=PORTEFEUILLES,
                             current_year=datetime.now().year)

# API Routes
@app.route('/api/search')
@cache.cached(timeout=300, query_string=True)
def search_tickers():
    """Enhanced search API"""
    query = request.args.get('q', '').lower()

    if len(query) < 2:
        return jsonify({'suggestions': []})

    results = []
    seen = set()

    for market, stocks in PORTEFEUILLES.items():
        for ticker, name in stocks.items():
            if query in ticker.lower() or query in name.lower():
                if ticker not in seen:
                    results.append({
                        'symbol': ticker,
                        'ticker': ticker,
                        'name': name,
                        'market': market
                    })
                    seen.add(ticker)
                    if len(results) >= 10:
                        break
        if len(results) >= 10:
            break

    if len(results) < 10:
        try:
            import yfinance as yf
            search_results = yf.Ticker(query.upper()).info
            if search_results and 'symbol' in search_results:
                ticker = search_results['symbol']
                if ticker not in seen:
                    market = 'EU' if any(x in ticker for x in ['.PA', '.DE', '.AS', '.L']) else 'US'
                    results.append({
                        'symbol': ticker,
                        'ticker': ticker,
                        'name': search_results.get('longName', search_results.get('shortName', ticker)),
                        'market': market
                    })
        except:
            pass

    return jsonify({'suggestions': results})

@app.route('/api/quote/<ticker>')
@cache.cached(timeout=60)
def get_quote_api(ticker):
    """Real-time quote API"""
    try:
        quote = fetcher.get_quote(ticker)
        return jsonify(quote)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache_api():
    """Clear cache API"""
    try:
        fetcher.clear_cache()
        cache.clear()
        return jsonify({'success': True, 'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    logger.info("🚀 Technical Analyst Started (OPTIMIZED)")
    logger.info("🌐 http://localhost:5000")

    try:
        test_quote = fetcher.get_quote("AAPL")
        logger.info(f"✅ System ready: AAPL = ${test_quote['price']:.2f}")
    except Exception as e:
        logger.warning(f"⚠️  Using mock data mode: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)