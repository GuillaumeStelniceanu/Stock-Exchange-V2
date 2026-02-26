#tests/test_data_fetcher.py
# tests/test_data_fetcher.py
import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.data_fetcher import OptimizedFetcher, MockSource, FastCache


class TestMockSource:
    def setup_method(self):
        self.source = MockSource()

    def test_get_stock_data_returns_dataframe(self):
        df = self.source.get_stock_data('AAPL', '6mo', '1d')
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_dataframe_has_required_columns(self):
        df = self.source.get_stock_data('AAPL', '6mo', '1d')
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required:
            assert col in df.columns

    def test_get_stock_info_returns_dict(self):
        info = self.source.get_stock_info('AAPL')
        assert info is not None
        assert isinstance(info, dict)
        assert 'name' in info
        assert 'symbol' in info

    def test_different_periods(self):
        for period in ['1mo', '3mo', '6mo', '1y']:
            df = self.source.get_stock_data('MSFT', period, '1d')
            assert df is not None and not df.empty


class TestOptimizedFetcher:
    def setup_method(self):
        self.fetcher = OptimizedFetcher(use_cache=False)

    def test_get_stock_data(self):
        df = self.fetcher.get_stock_data('AAPL', period='1mo')
        assert df is not None
        assert isinstance(df, pd.DataFrame)

    def test_get_quote(self):
        quote = self.fetcher.get_quote('AAPL')
        assert quote is not None
        assert 'price' in quote
        assert 'symbol' in quote

    def test_get_stock_info(self):
        info = self.fetcher.get_stock_info('AAPL')
        assert info is not None
        assert 'name' in info

    def test_source_stats(self):
        stats = self.fetcher.get_source_stats()
        assert isinstance(stats, dict)
        assert 'mock' in stats


class TestFastCache:
    def setup_method(self):
        self.cache = FastCache(cache_dir='/tmp/test_cache')

    def test_set_and_get(self):
        self.cache.set('test_key', {'value': 42}, 'test')
        result = self.cache.get('test_key', max_age_hours=1)
        assert result is not None
        assert result['value'] == 42

    def test_get_missing_key(self):
        result = self.cache.get('nonexistent_key', max_age_hours=1)
        assert result is None

    def test_clear(self):
        self.cache.set('key1', 'value1', 'test')
        self.cache.clear()
        result = self.cache.get('key1', max_age_hours=1)
        assert result is None