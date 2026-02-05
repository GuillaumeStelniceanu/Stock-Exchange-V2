# modules/technical_analysis.py - OPTIMIZED VERSION
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class FastTechnicalAnalysis:
    """Optimized technical analysis with vectorized operations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.results = {}
    
    def calculate_all(self) -> pd.DataFrame:
        """Calculate all indicators efficiently"""
        try:
            prices = self.df['Close'].values
            
            # Vectorized calculations
            self._calculate_moving_averages()
            self._calculate_rsi()
            self._calculate_macd()
            self._calculate_bollinger_bands()
            self._calculate_volume_indicators()
            self._generate_signals()
            
            return self.df
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return self.df
    
    def _calculate_moving_averages(self):
        """Fast MA calculation"""
        close = self.df['Close']
        for period in [20, 50, 200]:
            if len(self.df) >= period:
                self.df[f'MA_{period}'] = close.rolling(window=period).mean()
    
    def _calculate_rsi(self, period: int = 14):
        """Optimized RSI calculation"""
        if len(self.df) < period:
            return
        
        close = self.df['Close']
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.nan)
        self.df['RSI'] = 100 - (100 / (1 + rs))
    
    def _calculate_macd(self):
        """Fast MACD calculation"""
        close = self.df['Close']
        
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        
        self.df['MACD'] = exp1 - exp2
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=9, adjust=False).mean()
        self.df['MACD_Hist'] = self.df['MACD'] - self.df['MACD_Signal']
    
    def _calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2):
        """Fast Bollinger Bands"""
        close = self.df['Close']
        
        self.df['BB_Middle'] = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        self.df['BB_Upper'] = self.df['BB_Middle'] + (std * std_dev)
        self.df['BB_Lower'] = self.df['BB_Middle'] - (std * std_dev)
        self.df['BB_%B'] = (close - self.df['BB_Lower']) / (self.df['BB_Upper'] - self.df['BB_Lower'])
    
    def _calculate_volume_indicators(self):
        """Fast volume indicators"""
        volume = self.df['Volume']
        close = self.df['Close']
        
        # Volume MA
        self.df['Volume_MA20'] = volume.rolling(window=20).mean()
        
        # OBV (vectorized)
        price_diff = np.sign(close.diff())
        obv = (price_diff * volume).cumsum()
        self.df['OBV'] = obv
    
    def _generate_signals(self):
        """Generate trading signals efficiently"""
        signals = []
        
        if len(self.df) < 2:
            self.results['signals'] = signals
            return
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # RSI signals
        if 'RSI' in latest and not pd.isna(latest['RSI']):
            rsi = latest['RSI']
            if rsi > 70:
                signals.append({
                    'type': 'danger',
                    'title': 'RSI Surachat',
                    'description': f"RSI à {rsi:.1f} > 70 - Signal de vente",
                    'value': rsi
                })
            elif rsi < 30:
                signals.append({
                    'type': 'success',
                    'title': 'RSI Survente',
                    'description': f"RSI à {rsi:.1f} < 30 - Signal d'achat",
                    'value': rsi
                })
        
        # MACD crossover
        if all(col in latest for col in ['MACD', 'MACD_Signal']):
            if latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
                signals.append({
                    'type': 'success',
                    'title': 'MACD Croisement Haussier',
                    'description': "MACD croise au-dessus du signal",
                    'icon': 'arrow-up'
                })
            elif latest['MACD'] < latest['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
                signals.append({
                    'type': 'danger',
                    'title': 'MACD Croisement Baissier',
                    'description': "MACD croise en-dessous du signal",
                    'icon': 'arrow-down'
                })
        
        # Volume spike
        if all(col in latest for col in ['Volume', 'Volume_MA20']):
            if latest['Volume'] > latest['Volume_MA20'] * 1.5:
                signals.append({
                    'type': 'warning',
                    'title': 'Volume Élevé',
                    'description': f"Volume {latest['Volume'] / latest['Volume_MA20']:.1f}x la moyenne",
                    'icon': 'chart-bar'
                })
        
        self.results['signals'] = signals
    
    def get_summary(self) -> Dict:
        """Get analysis summary"""
        if len(self.df) < 2:
            return {}
        
        latest = self.df.iloc[-1]
        
        return {
            'last_price': float(latest['Close']),
            'rsi': float(latest.get('RSI', 0)) if 'RSI' in latest else None,
            'macd': float(latest.get('MACD', 0)) if 'MACD' in latest else None,
            'bb_position': float(latest.get('BB_%B', 0)) if 'BB_%B' in latest else None,
            'volume_ratio': float(latest['Volume'] / latest['Volume_MA20']) if 'Volume_MA20' in latest else None,
            'signals': self.results.get('signals', [])
        }