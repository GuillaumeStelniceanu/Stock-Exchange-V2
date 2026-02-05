#tests/test_indicators.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.indicators import TechnicalIndicators
from modules.technical_analysis import TechnicalAnalysis

@pytest.fixture
def sample_data():
    """Crée des données d'exemple pour les tests"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    np.random.seed(42)
    base_price = 100
    prices = []
    
    for i in range(100):
        if i == 0:
            prices.append(base_price)
        else:
            change = np.random.normal(0, 1)  # Changement quotidien aléatoire
            prices.append(prices[-1] + change)
    
    df = pd.DataFrame({
        'Open': prices,
        'High': [p + np.random.random() for p in prices],
        'Low': [p - np.random.random() for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    return df

class TestTechnicalIndicators:
    """Tests pour la classe TechnicalIndicators"""
    
    def test_calculate_rsi(self, sample_data):
        """Test du calcul du RSI"""
        rsi = TechnicalIndicators.calculate_rsi(sample_data['Close'], period=14)
        
        # Vérifications de base
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_data)
        assert not rsi.isna().all()  # Ne devrait pas être tout NaN
        
        # Le RSI devrait être entre 0 et 100
        if not rsi.isna().all():
            assert rsi.max() <= 100
            assert rsi.min() >= 0
    
    def test_calculate_macd(self, sample_data):
        """Test du calcul du MACD"""
        macd_results = TechnicalIndicators.calculate_macd(sample_data['Close'])
        
        # Vérifier que tous les composants sont présents
        assert 'macd' in macd_results
        assert 'signal' in macd_results
        assert 'histogram' in macd_results
        
        # Vérifier les types
        assert isinstance(macd_results['macd'], pd.Series)
        assert isinstance(macd_results['signal'], pd.Series)
        assert isinstance(macd_results['histogram'], pd.Series)
        
        # Vérifier les longueurs
        assert len(macd_results['macd']) == len(sample_data)
    
    def test_calculate_bollinger_bands(self, sample_data):
        """Test du calcul des bandes de Bollinger"""
        bb_results = TechnicalIndicators.calculate_bollinger_bands(sample_data['Close'])
        
        # Vérifier que tous les composants sont présents
        required_keys = ['middle', 'upper', 'lower', 'bandwidth', 'percent_b']
        for key in required_keys:
            assert key in bb_results
            assert isinstance(bb_results[key], pd.Series)
        
        # Vérifier les relations
        if not bb_results['upper'].isna().all():
            # La bande supérieure devrait être > bande moyenne > bande inférieure
            for i in range(len(sample_data)):
                if not (pd.isna(bb_results['upper'].iloc[i]) or 
                       pd.isna(bb_results['middle'].iloc[i]) or 
                       pd.isna(bb_results['lower'].iloc[i])):
                    assert bb_results['upper'].iloc[i] >= bb_results['middle'].iloc[i]
                    assert bb_results['middle'].iloc[i] >= bb_results['lower'].iloc[i]
    
    def test_calculate_atr(self, sample_data):
        """Test du calcul de l'ATR"""
        atr = TechnicalIndicators.calculate_atr(
            sample_data['High'], 
            sample_data['Low'], 
            sample_data['Close']
        )
        
        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_data)
        
        # L'ATR ne devrait pas être négatif
        if not atr.isna().all():
            assert atr.min() >= 0
    
    def test_calculate_moving_averages(self, sample_data):
        """Test du calcul des moyennes mobiles"""
        periods = [20, 50, 200]
        ma_results = TechnicalIndicators.calculate_moving_averages(sample_data['Close'], periods)
        
        # Vérifier toutes les périodes
        for period in periods:
            key = f'ma_{period}'
            assert key in ma_results
            assert isinstance(ma_results[key], pd.Series)
            
            # Pour les périodes courtes, il devrait y avoir des valeurs non-NaN
            if period <= 50:
                assert not ma_results[key].isna().all()

class TestTechnicalAnalysis:
    """Tests pour la classe TechnicalAnalysis"""
    
    def test_initialization(self, sample_data):
        """Test de l'initialisation"""
        analyzer = TechnicalAnalysis(sample_data)
        
        assert analyzer.df is not None
        assert analyzer.price is not None
        assert analyzer.results == {}
    
    def test_calculate_all(self, sample_data):
        """Test du calcul complet des indicateurs"""
        analyzer = TechnicalAnalysis(sample_data)
        result_df = analyzer.calculate_all()
        
        # Vérifier que des indicateurs ont été ajoutés
        expected_columns = ['MA_20', 'MA_50', 'RSI', 'MACD', 'BB_Middle']
        for col in expected_columns:
            assert col in result_df.columns
        
        # Vérifier que les signaux ont été générés
        assert 'signals' in analyzer.results
    
    def test_get_summary(self, sample_data):
        """Test de la génération du résumé"""
        analyzer = TechnicalAnalysis(sample_data)
        analyzer.calculate_all()
        summary = analyzer.get_summary()
        
        # Vérifier la structure du résumé
        expected_keys = ['last_price', 'rsi', 'macd', 'bb_position', 
                        'atr', 'volume_ratio', 'signals', 'trend']
        
        for key in expected_keys:
            assert key in summary
        
        # Vérifier les types
        assert isinstance(summary['last_price'], float)
        assert isinstance(summary['signals'], list)

def test_empty_data():
    """Test avec des données vides"""
    empty_df = pd.DataFrame()
    analyzer = TechnicalAnalysis(empty_df)
    
    # Ne devrait pas planter
    result = analyzer.calculate_all()
    assert result.empty
    
    summary = analyzer.get_summary()
    assert summary == {}

def test_minimal_data():
    """Test avec le minimum de données"""
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    df = pd.DataFrame({
        'Open': [100, 101, 102, 101, 100],
        'High': [101, 102, 103, 102, 101],
        'Low': [99, 100, 101, 100, 99],
        'Close': [100, 101, 102, 101, 100],
        'Volume': [1000, 2000, 1500, 1800, 1200]
    }, index=dates)
    
    analyzer = TechnicalAnalysis(df)
    result = analyzer.calculate_all()
    
    # Certains indicateurs ne pourront pas être calculés avec peu de données
    # Mais ne devrait pas planter
    assert not result.empty

if __name__ == '__main__':
    pytest.main([__file__, '-v'])