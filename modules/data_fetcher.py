# modules/data_fetcher.py - OPTIMIZED VERSION
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import time
import requests
import os
from pathlib import Path
import pickle
import hashlib

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
class Config:
    """Configuration centralisée"""
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
    FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
    TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'demo')
    
    SOURCE_PRIORITIES = {
        'yfinance': 4,        # Most reliable, free
        'alpha_vantage': 3,
        'twelve_data': 2,
        'fmp': 1,
        'mock': 0
    }
    
    CACHE_DIR = "data_cache"
    CACHE_DURATION_HISTORY = 6  # hours
    CACHE_DURATION_INFO = 24    # hours
    
    RATE_LIMITS = {  # requests per minute
        'alpha_vantage': 5,
        'fmp': 2,
        'twelve_data': 8,
        'yfinance': 30
    }
    
    REQUEST_TIMEOUT = 10  # seconds

# ==================== OPTIMIZED CACHE ====================
class FastCache:
    """Optimized cache with memory + disk"""
    
    def __init__(self, cache_dir: str = Config.CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._memory = {}  # In-memory cache
        self._access_times = {}  # Track access for LRU
        self._max_memory_items = 100
    
    def _get_key_hash(self, key: str) -> str:
        """Fast hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str, max_age_hours: int = 24):
        """Get from cache (memory first, then disk)"""
        # Check memory cache
        if key in self._memory:
            data, timestamp = self._memory[key]
            if (datetime.now() - timestamp).total_seconds() < max_age_hours * 3600:
                self._access_times[key] = time.time()
                return data
            del self._memory[key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{self._get_key_hash(key)}.pkl"
        if cache_file.exists():
            try:
                age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
                if age_hours < max_age_hours:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    # Store in memory for next access
                    self._memory[key] = (data, datetime.now())
                    self._access_times[key] = time.time()
                    self._cleanup_memory()
                    return data
                cache_file.unlink()  # Delete expired
            except Exception as e:
                logger.debug(f"Cache read error: {e}")
                try:
                    cache_file.unlink()
                except:
                    pass
        
        return None
    
    def set(self, key: str, data, source: str = None):
        """Store in cache"""
        timestamp = datetime.now()
        
        # Memory cache
        self._memory[key] = (data, timestamp)
        self._access_times[key] = time.time()
        self._cleanup_memory()
        
        # Disk cache
        cache_file = self.cache_dir / f"{self._get_key_hash(key)}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.debug(f"Cache write error: {e}")
    
    def _cleanup_memory(self):
        """LRU cleanup of memory cache"""
        if len(self._memory) > self._max_memory_items:
            # Remove least recently used
            sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
            to_remove = sorted_keys[:len(self._memory) - self._max_memory_items]
            for key, _ in to_remove:
                self._memory.pop(key, None)
                self._access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self._memory.clear()
        self._access_times.clear()
        for f in self.cache_dir.glob("*.pkl"):
            try:
                f.unlink()
            except:
                pass

# ==================== BASE SOURCE ====================
class DataSource:
    """Optimized base source"""
    
    def __init__(self, name: str, priority: int):
        self.name = name
        self.priority = priority
        self.enabled = True
        self._last_request = 0
        self._error_count = 0
    
    def _rate_limit(self):
        """Fast rate limiting"""
        if self.name in Config.RATE_LIMITS:
            interval = 60.0 / Config.RATE_LIMITS[self.name]
            elapsed = time.time() - self._last_request
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_request = time.time()
    
    def is_available(self) -> bool:
        return self.enabled and self._error_count < 5
    
    def _mark_error(self):
        self._error_count += 1
        if self._error_count >= 5:
            self.enabled = False
    
    def _mark_success(self):
        self._error_count = max(0, self._error_count - 1)

# ==================== YFINANCE SOURCE (FASTEST) ====================
class YFinanceSource(DataSource):
    """Optimized YFinance - Primary source"""
    
    def __init__(self):
        super().__init__('yfinance', Config.SOURCE_PRIORITIES['yfinance'])
        self._yf = None
    
    def _get_yf(self):
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                self._yf = False
                self.enabled = False
        return self._yf
    
    def get_stock_data(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        yf = self._get_yf()
        if not yf or not self.is_available():
            return None
        
        self._rate_limit()
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval, timeout=Config.REQUEST_TIMEOUT)
            
            if not df.empty:
                # Standardize columns
                if 'Adj Close' in df.columns:
                    df['Close'] = df['Adj Close']
                
                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                df = df[required]
                
                self._mark_success()
                return df
                
        except Exception as e:
            logger.debug(f"YFinance error for {ticker}: {e}")
            self._mark_error()
        
        return None
    
    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        yf = self._get_yf()
        if not yf or not self.is_available():
            return None
        
        self._rate_limit()
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if info and 'symbol' in info:
                self._mark_success()
                return {
                    'symbol': ticker,
                    'name': info.get('longName', ticker),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'currency': info.get('currency', 'USD'),
                    'marketCap': info.get('marketCap', 0),
                    'peRatio': info.get('trailingPE', 0),
                    'dividendYield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 0),
                    'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 0),
                    'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 0),
                    'source': self.name
                }
        except Exception as e:
            logger.debug(f"YFinance info error: {e}")
            self._mark_error()
        
        return None

# ==================== MOCK SOURCE ====================
class MockSource(DataSource):
    """Fast mock data generator"""
    
    def __init__(self):
        super().__init__('mock', Config.SOURCE_PRIORITIES['mock'])
        self._cache = {}
    
    def get_stock_data(self, ticker: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        if interval != '1d':
            return None
        
        # Use cached mock data
        if ticker in self._cache:
            return self._cache[ticker].copy()
        
        # Generate mock data
        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        days = days_map.get(period, 180)
        
        dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
        
        # Deterministic price based on ticker
        base_price = 50 + (hash(ticker) % 150)
        np.random.seed(abs(hash(ticker)) % 10000)
        
        returns = np.random.normal(0.0005, 0.015, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # Ensure OHLC logic
        df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
        df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)
        
        self._cache[ticker] = df
        return df.copy()
    
    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        companies = {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.', 'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.', 'META': 'Meta Platforms Inc.', 'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corp.', 'TTE.PA': 'TotalEnergies SE'
        }
        
        return {
            'symbol': ticker,
            'name': companies.get(ticker, f"{ticker} Corporation"),
            'sector': 'Technology',
            'currency': 'EUR' if '.PA' in ticker else 'USD',
            'price': 50 + (hash(ticker) % 150),
            'source': 'mock'
        }

# ==================== MAIN FETCHER ====================
class OptimizedFetcher:
    """Optimized multi-source fetcher"""
    
    def __init__(self, use_cache: bool = True):
        self.cache = FastCache() if use_cache else None
        self.sources = [
            YFinanceSource(),  # Primary - fast & reliable
            MockSource()       # Fallback
        ]
        self.sources.sort(key=lambda x: x.priority, reverse=True)
        logger.info(f"Fetcher initialized with {len(self.sources)} sources")
    
    def get_stock_data(self, ticker: str, period: str = "6mo", 
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """Get stock data (cached)"""
        cache_key = f"data_{ticker}_{period}_{interval}"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(cache_key, Config.CACHE_DURATION_HISTORY)
            if cached is not None and isinstance(cached, pd.DataFrame):
                return cached.copy()
        
        # Try sources
        for source in self.sources:
            if not source.is_available():
                continue
            
            try:
                df = source.get_stock_data(ticker, period, interval)
                if df is not None and not df.empty:
                    # Validate and clean
                    df = self._clean_data(df)
                    if not df.empty:
                        if self.cache:
                            self.cache.set(cache_key, df, source.name)
                        logger.info(f"✓ {ticker} from {source.name}")
                        return df
            except Exception as e:
                logger.debug(f"{source.name} failed: {e}")
        
        logger.warning(f"All sources failed for {ticker}")
        return None
    
    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get stock info (cached)"""
        cache_key = f"info_{ticker}"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(cache_key, Config.CACHE_DURATION_INFO)
            if cached:
                return cached
        
        # Try sources
        for source in self.sources:
            if not source.is_available():
                continue
            
            try:
                info = source.get_stock_info(ticker)
                if info and isinstance(info, dict) and 'symbol' in info:
                    if self.cache:
                        self.cache.set(cache_key, info, source.name)
                    return info
            except Exception as e:
                logger.debug(f"{source.name} info failed: {e}")
        
        return None
    
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Get current quote"""
        try:
            df = self.get_stock_data(ticker, period="5d", interval="1d")
            
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                return {
                    'symbol': ticker,
                    'price': float(latest['Close']),
                    'change': float(latest['Close'] - prev['Close']),
                    'changePercent': float(((latest['Close'] - prev['Close']) / prev['Close']) * 100),
                    'volume': int(latest['Volume']),
                    'timestamp': datetime.now().isoformat()
                }
        except:
            pass
        
        # Fallback
        price = 50 + (hash(ticker) % 150)
        return {
            'symbol': ticker,
            'price': price,
            'change': 0,
            'changePercent': 0,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat()
        }
    
    def search_tickers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tickers"""
        query = query.lower()
        results = []
        
        tickers = {
            'AAPL': 'Apple Inc.', 'MSFT': 'Microsoft Corp.',
            'GOOGL': 'Alphabet Inc.', 'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.', 'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corp.', 'TTE.PA': 'TotalEnergies SE'
        }
        
        for symbol, name in tickers.items():
            if query in symbol.lower() or query in name.lower():
                info = self.get_stock_info(symbol)
                if info:
                    results.append(info)
                if len(results) >= limit:
                    break
        
        return results
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fast data cleaning"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Ensure all required columns exist
        for col in required:
            if col not in df.columns:
                df[col] = df.get('Close', 0) if col != 'Volume' else 0
        
        # Convert to numeric
        for col in required:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop invalid rows
        df = df.dropna(subset=['Close'])
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        return df[required].sort_index()
    
    def clear_cache(self):
        """Clear cache"""
        if self.cache:
            self.cache.clear()
    
    def get_source_stats(self) -> Dict[str, Any]:
        """Get source statistics"""
        return {
            source.name: {
                'available': source.is_available(),
                'priority': source.priority,
                'enabled': source.enabled
            }
            for source in self.sources
        }

# Singleton instance
default_fetcher = OptimizedFetcher(use_cache=True)