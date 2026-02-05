#config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-2024-technical-analysis')
    
    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    
    # API Keys (si nécessaire)
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', '')
    FINNHUB_KEY = os.getenv('FINNHUB_KEY', '')
    
    # Configuration des marchés
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
            "HD": "Home Depot",
            "MA": "Mastercard",
            "BAC": "Bank of America",
            "DIS": "Walt Disney",
            "NFLX": "Netflix",
            "ADBE": "Adobe Inc."
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
            "ASML.AS": "ASML Holding",
            "AIR.DE": "Airbus SE",
            "SIEGY": "Siemens AG",
            "NOVOb.CO": "Novo Nordisk",
            "HSBA.L": "HSBC Holdings",
            "BP.L": "BP plc",
            "ULVR.L": "Unilever",
            "AZN.L": "AstraZeneca",
            "SHEL.L": "Shell plc"
        },
        "SECTEURS": {
            "XLE": "Énergie SPDR",
            "XLF": "Finances SPDR",
            "XLV": "Santé SPDR",
            "XLK": "Technologie SPDR",
            "XLY": "Cycliques SPDR",
            "XLP": "Consommation courante SPDR",
            "XLI": "Industriels SPDR",
            "XLU": "Services publics SPDR",
            "XLRE": "Immobilier SPDR",
            "XLB": "Matériaux SPDR",
            "ARKK": "ARK Innovation ETF",
            "QQQ": "Invesco QQQ Trust",
            "SPY": "SPDR S&P 500 ETF",
            "VTI": "Vanguard Total Stock Market",
            "VOO": "Vanguard S&P 500 ETF"
        },
        "CRYPTO": {
            "BTC-USD": "Bitcoin USD",
            "ETH-USD": "Ethereum USD",
            "BNB-USD": "Binance Coin USD",
            "ADA-USD": "Cardano USD",
            "SOL-USD": "Solana USD",
            "XRP-USD": "Ripple USD",
            "DOT-USD": "Polkadot USD",
            "DOGE-USD": "Dogecoin USD",
            "AVAX-USD": "Avalanche USD",
            "SHIB-USD": "Shiba Inu USD"
        }
    }
    
    # Périodes disponibles
    PERIODS = {
        '1d': '1 Jour',
        '5d': '5 Jours',
        '1mo': '1 Mois',
        '3mo': '3 Mois',
        '6mo': '6 Mois',
        '1y': '1 An',
        '2y': '2 Ans',
        '5y': '5 Ans',
        'max': 'Max'
    }
    
    INTERVALS = {
        '1d': '1m',
        '5d': '5m',
        '1mo': '30m',
        '3mo': '1d',
        '6mo': '1d',
        '1y': '1d',
        '2y': '1d',
        '5y': '1wk',
        'max': '1mo'
    }
    
    # Configuration technique
    DEFAULT_PERIOD = '6mo'
    DEFAULT_INTERVAL = '1d'
    
    # Configuration des indicateurs
    INDICATORS = {
        'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
        'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
        'MA': {'periods': [20, 50, 200]},
        'BB': {'period': 20, 'std': 2},
        'ATR': {'period': 14},
        'STOCH': {'k': 14, 'd': 3}
    }
    
    # Couleurs des indicateurs
    CHART_COLORS = {
        'candle_up': '#26a69a',
        'candle_down': '#ef5350',
        'ma_20': '#FF9800',
        'ma_50': '#2196F3',
        'ma_200': '#9C27B0',
        'bb_upper': '#757575',
        'bb_lower': '#757575',
        'volume_up': 'rgba(38, 166, 154, 0.7)',
        'volume_down': 'rgba(239, 83, 80, 0.7)',
        'rsi': '#FFEB3B',
        'macd': '#00BCD4',
        'macd_signal': '#E91E63',
        'atr': '#8BC34A'
    }
    
    # Configuration des signaux
    SIGNAL_CONFIG = {
        'rsi_overbought': 70,
        'rsi_oversold': 30,
        'macd_bullish_threshold': 0,
        'macd_bearish_threshold': 0,
        'volume_multiplier': 1.5
    }