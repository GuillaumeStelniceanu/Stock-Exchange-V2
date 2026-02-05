#modules/indicators.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging
from scipy import stats

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Collection de fonctions pour calculer les indicateurs techniques"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcule le RSI (Relative Strength Index)"""
        if len(prices) < period:
            return pd.Series(index=prices.index, dtype=float)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Éviter la division par zéro
        loss = loss.replace(0, np.nan)
        rs = gain / loss
        
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, 
                      signal: int = 9) -> Dict[str, pd.Series]:
        """Calcule le MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {
                'macd': pd.Series(index=prices.index, dtype=float),
                'signal': pd.Series(index=prices.index, dtype=float),
                'histogram': pd.Series(index=prices.index, dtype=float)
            }
        
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, 
                                 std_dev: float = 2) -> Dict[str, pd.Series]:
        """Calcule les bandes de Bollinger"""
        if len(prices) < period:
            return {
                'middle': pd.Series(index=prices.index, dtype=float),
                'upper': pd.Series(index=prices.index, dtype=float),
                'lower': pd.Series(index=prices.index, dtype=float),
                'bandwidth': pd.Series(index=prices.index, dtype=float),
                'percent_b': pd.Series(index=prices.index, dtype=float)
            }
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # Bandwidth
        bandwidth = ((upper - lower) / middle) * 100
        
        # %B
        percent_b = (prices - lower) / (upper - lower)
        
        return {
            'middle': middle,
            'upper': upper,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """Calcule l'ATR (Average True Range)"""
        if len(high) < period:
            return pd.Series(index=high.index, dtype=float)
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calcule l'oscillateur stochastique"""
        if len(high) < k_period:
            return {
                'k': pd.Series(index=high.index, dtype=float),
                'd': pd.Series(index=high.index, dtype=float)
            }
        
        # %K
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # %D (moyenne mobile de %K)
        d = k.rolling(window=d_period).mean()
        
        return {'k': k, 'd': d}
    
    @staticmethod
    def calculate_ichimoku(high: pd.Series, low: pd.Series, 
                          conversion_period: int = 9, 
                          base_period: int = 26,
                          leading_span_period: int = 52,
                          displacement: int = 26) -> Dict[str, pd.Series]:
        """Calcule les nuages d'Ichimoku"""
        if len(high) < leading_span_period:
            return {}
        
        # Conversion Line (Tenkan-sen)
        conversion_line = (high.rolling(window=conversion_period).max() + 
                         low.rolling(window=conversion_period).min()) / 2
        
        # Base Line (Kijun-sen)
        base_line = (high.rolling(window=base_period).max() + 
                    low.rolling(window=base_period).min()) / 2
        
        # Leading Span A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # Leading Span B (Senkou Span B)
        leading_span_b = ((high.rolling(window=leading_span_period).max() + 
                          low.rolling(window=leading_span_period).min()) / 2).shift(displacement)
        
        # Lagging Span (Chikou Span)
        lagging_span = low.shift(-displacement)
        
        return {
            'conversion': conversion_line,
            'base': base_line,
            'leading_a': leading_span_a,
            'leading_b': leading_span_b,
            'lagging': lagging_span
        }
    
    @staticmethod
    def calculate_volume_indicators(volume: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Calcule les indicateurs de volume"""
        # On Balance Volume (OBV)
        obv = pd.Series(index=volume.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(volume)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        # Volume Weighted Average Price (VWAP)
        # Nécessite des données intraday
        vwap = pd.Series(index=volume.index, dtype=float)
        
        # Pour les données quotidiennes, on calcule une approximation
        typical_price = (close + close.shift() + close.shift(2)) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        return {
            'obv': obv,
            'vwap': vwap,
            'volume_ma': volume.rolling(window=20).mean()
        }
    
    @staticmethod
    def calculate_moving_averages(prices: pd.Series, periods: List[int]) -> Dict[str, pd.Series]:
        """Calcule plusieurs moyennes mobiles"""
        result = {}
        
        for period in periods:
            if len(prices) >= period:
                result[f'ma_{period}'] = prices.rolling(window=period).mean()
            else:
                result[f'ma_{period}'] = pd.Series(index=prices.index, dtype=float)
        
        return result
    
    @staticmethod
    def calculate_parabolic_sar(high: pd.Series, low: pd.Series, 
                               acceleration: float = 0.02, 
                               maximum: float = 0.2) -> pd.Series:
        """Calcule le Parabolic SAR"""
        if len(high) < 2:
            return pd.Series(index=high.index, dtype=float)
        
        sar = pd.Series(index=high.index, dtype=float)
        trend = 1  # 1 = haussier, -1 = baissier
        af = acceleration
        ep = high.iloc[0] if trend == 1 else low.iloc[0]
        sar.iloc[0] = low.iloc[0] if trend == 1 else high.iloc[0]
        
        for i in range(1, len(high)):
            # SAR précédent
            prev_sar = sar.iloc[i-1]
            
            if trend == 1:  # Tendance haussière
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                
                # Vérifier si le SAR est au-dessus du plus bas
                if sar.iloc[i] > low.iloc[i]:
                    sar.iloc[i] = low.iloc[i]
                
                # Mettre à jour EP et AF
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + acceleration, maximum)
                
                # Vérifier l'inversion de tendance
                if sar.iloc[i] > low.iloc[i]:
                    trend = -1
                    sar.iloc[i] = ep
                    ep = low.iloc[i]
                    af = acceleration
            
            else:  # Tendance baissière
                sar.iloc[i] = prev_sar + af * (ep - prev_sar)
                
                # Vérifier si le SAR est en dessous du plus haut
                if sar.iloc[i] < high.iloc[i]:
                    sar.iloc[i] = high.iloc[i]
                
                # Mettre à jour EP et AF
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + acceleration, maximum)
                
                # Vérifier l'inversion de tendance
                if sar.iloc[i] < high.iloc[i]:
                    trend = 1
                    sar.iloc[i] = ep
                    ep = high.iloc[i]
                    af = acceleration
        
        return sar
    
    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, 
                     period: int = 14) -> Dict[str, pd.Series]:
        """Calcule l'ADX (Average Directional Index)"""
        if len(high) < period * 2:
            return {
                'adx': pd.Series(index=high.index, dtype=float),
                'plus_di': pd.Series(index=high.index, dtype=float),
                'minus_di': pd.Series(index=high.index, dtype=float)
            }
        
        # Plus et moins Directional Movement
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = abs(minus_dm)
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smooth les valeurs
        plus_dm_smooth = plus_dm.rolling(window=period).mean()
        minus_dm_smooth = minus_dm.rolling(window=period).mean()
        tr_smooth = tr.rolling(window=period).mean()
        
        # Directional Indicators
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Directional Index
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def calculate_pivot_points(high: pd.Series, low: pd.Series, 
                              close: pd.Series) -> Dict[str, pd.Series]:
        """Calcule les points pivots"""
        pivot = (high + low + close) / 3
        
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1,
            's1': s1,
            'r2': r2,
            's2': s2,
            'r3': r3,
            's3': s3
        }
    
    @staticmethod
    def calculate_fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
        """Calcule les niveaux de retracement Fibonacci"""
        diff = high - low
        
        levels = {
            'fib_0.0': high,
            'fib_0.236': high - 0.236 * diff,
            'fib_0.382': high - 0.382 * diff,
            'fib_0.5': high - 0.5 * diff,
            'fib_0.618': high - 0.618 * diff,
            'fib_0.786': high - 0.786 * diff,
            'fib_1.0': low,
            'fib_1.272': low - 0.272 * diff,
            'fib_1.618': low - 0.618 * diff
        }
        
        return levels
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20, 
                                   num_levels: int = 5) -> Dict[str, List[float]]:
        """Calcule les niveaux de support et résistance"""
        if len(df) < window:
            return {'supports': [], 'resistances': []}
        
        high = df['High'].tail(window)
        low = df['Low'].tail(window)
        close = df['Close'].tail(window)
        
        # Utiliser les clusters de prix
        all_prices = pd.concat([high, low, close])
        
        # Regrouper les prix proches
        price_groups = []
        prices_sorted = all_prices.sort_values()
        
        cluster = []
        for price in prices_sorted:
            if not cluster:
                cluster.append(price)
            elif abs(price - cluster[-1]) <= (all_prices.max() - all_prices.min()) * 0.01:
                cluster.append(price)
            else:
                price_groups.append(cluster)
                cluster = [price]
        
        if cluster:
            price_groups.append(cluster)
        
        # Calculer les niveaux (moyenne de chaque groupe)
        levels = [sum(group) / len(group) for group in price_groups if len(group) > 1]
        levels = sorted(levels)
        
        # Séparer supports et résistances
        current_price = close.iloc[-1]
        
        supports = [level for level in levels if level < current_price]
        resistances = [level for level in levels if level > current_price]
        
        # Garder seulement les N niveaux les plus proches
        supports = sorted(supports, reverse=True)[:num_levels]
        resistances = sorted(resistances)[:num_levels]
        
        return {
            'supports': supports,
            'resistances': resistances
        }