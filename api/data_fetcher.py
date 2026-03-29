"""
Data Fetcher Module

This module handles fetching stock data from yfinance API and processing it
with various calculated metrics including moving averages, returns, and volatility.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


class StockDataFetcher:
    """
    A class to fetch and process stock market data using yfinance.
    
    Attributes:
        symbol (str): The stock ticker symbol
        data (pd.DataFrame): The processed stock data
    """
    
    def __init__(self, symbol: str):
        """
        Initialize the StockDataFetcher with a stock symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'INFY.NS', 'AAPL')
        """
        self.symbol = symbol.upper()
        self.data: Optional[pd.DataFrame] = None
        self._raw_data: Optional[pd.DataFrame] = None
    
    async def fetch_data(self, period: str = "1y") -> pd.DataFrame:
        """
        Fetch stock data from yfinance for the specified period.
        
        Args:
            period: Time period for data fetching (default: '1y' for 1 year)
        
        Returns:
            DataFrame with raw stock data
            
        Raises:
            ValueError: If no data is found for the symbol
        """
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Fetching data for {self.symbol} (attempt {attempt + 1}/{MAX_RETRIES})")
                ticker = yf.Ticker(self.symbol)
                self._raw_data = ticker.history(period=period, timeout=30)
                
                if self._raw_data.empty:
                    # Try alternate symbol format
                    if '.NS' in self.symbol and attempt < MAX_RETRIES - 1:
                        logger.info(f"Retrying with different format for {self.symbol}")
                        time.sleep(RETRY_DELAY)
                        continue
                    raise ValueError(f"No data found for symbol: {self.symbol}")
                
                logger.info(f"Successfully fetched {len(self._raw_data)} records for {self.symbol}")
                return self._raw_data
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for {self.symbol}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                continue
        
        logger.error(f"All {MAX_RETRIES} attempts failed for {self.symbol}: {str(last_error)}")
        raise last_error or ValueError(f"Failed to fetch data for {self.symbol} after {MAX_RETRIES} attempts")
    
    def clean_data(self) -> pd.DataFrame:
        """
        Clean the raw stock data by handling missing values and formatting.
        
        Returns:
            Cleaned DataFrame
            
        Raises:
            ValueError: If no raw data is available
        """
        if self._raw_data is None or self._raw_data.empty:
            raise ValueError("No raw data available. Call fetch_data() first.")
        
        df = self._raw_data.copy()
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Rename columns for consistency
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Handle missing values
        # Forward fill for price data (use previous day's value)
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col].ffill()
        
        # Fill volume with 0 if missing
        if 'volume' in df.columns:
            df['volume'] = df['volume'].fillna(0)
        
        # Drop any remaining rows with NaN in critical columns
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        # Ensure proper data types
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        
        for col in price_columns:
            df[col] = df[col].astype(float)
        
        if 'volume' in df.columns:
            df['volume'] = df['volume'].astype(int)
        
        logger.info(f"Data cleaned. Records: {len(df)}")
        return df
    
    def add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add calculated metrics to the stock data.
        
        Calculated fields:
        - daily_return: (Close - Open) / Open
        - ma_7: 7-day moving average of closing price
        - ma_20: 20-day moving average
        - ma_50: 50-day moving average
        - high_52w: 52-week high
        - low_52w: 52-week low
        - volatility: Rolling standard deviation of returns (20-day window)
        - RSI: Relative Strength Index (14-day)
        - MACD: Moving Average Convergence Divergence
        - MACD_Signal: MACD signal line
        - MACD_Histogram: MACD histogram
        - BB_Upper: Bollinger Bands Upper
        - BB_Lower: Bollinger Bands Lower
        - BB_Middle: Bollinger Bands Middle
        - ATR: Average True Range (14-day)
        - FVG: Fair Value Gap (bullish/bearish gaps)
        
        Args:
            df: Cleaned stock data DataFrame
            
        Returns:
            DataFrame with additional calculated fields
        """
        df = df.copy()
        
        # Daily Return = (Close - Open) / Open
        df['daily_return'] = (df['close'] - df['open']) / df['open']
        
        # Simple Returns
        df['simple_return'] = df['close'].pct_change()
        
        # Moving Averages
        df['ma_7'] = df['close'].rolling(window=7, min_periods=1).mean()
        df['ma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['ma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
        df['ma_200'] = df['close'].rolling(window=200, min_periods=1).mean()
        
        # 52-week High and Low (rolling)
        trading_days_year = min(252, len(df))
        df['high_52w'] = df['high'].rolling(window=trading_days_year, min_periods=1).max()
        df['low_52w'] = df['low'].rolling(window=trading_days_year, min_periods=1).min()
        
        # Volatility (rolling standard deviation of daily returns, 20-day window)
        df['volatility'] = df['daily_return'].rolling(window=20, min_periods=1).std()
        df['volatility_annualized'] = df['volatility'] * np.sqrt(252)
        
        # Price change from previous day
        df['price_change'] = df['close'].diff()
        df['price_change_pct'] = df['close'].pct_change() * 100
        
        # RSI (Relative Strength Index) - 14 day
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
        
        # MACD (Moving Average Convergence Divergence)
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands (20-day, 2 standard deviations)
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR (Average True Range) - 14 day
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Fair Value Gap (FVG) Detection
        # Bullish FVG: gap between current candle high and previous candle low
        df['fvg_bullish'] = (df['low'] > df['high'].shift(2)) & \
                            (df['low'].shift(1) > df['high'].shift(2))
        df['fvg_bearish'] = (df['high'] < df['low'].shift(2)) & \
                           (df['high'].shift(1) < df['low'].shift(2))
        df['fvg_bullish'] = df['fvg_bullish'].astype(int)
        df['fvg_bearish'] = df['fvg_bearish'].astype(int)
        
        # Gap size for FVG
        df['fvg_size'] = np.where(
            df['fvg_bullish'] == 1,
            df['low'] - df['high'].shift(2),
            np.where(df['fvg_bearish'] == 1, df['low'].shift(2) - df['high'], 0)
        )
        
        # Trend Detection
        df['trend'] = np.where(df['close'] > df['ma_50'], 'Bullish',
                              np.where(df['close'] < df['ma_50'], 'Bearish', 'Neutral'))
        df['trend_strength'] = abs(df['close'] - df['ma_50']) / df['ma_50'] * 100
        
        # Support and Resistance levels
        df['support'] = df['low'].rolling(window=20).min()
        df['resistance'] = df['high'].rolling(window=20).max()
        
        # Volume analysis
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        logger.info("Calculated fields added successfully")
        return df
    
    async def process(self) -> pd.DataFrame:
        """
        Execute the full data processing pipeline.
        
        Returns:
            Fully processed DataFrame with all calculated fields
        """
        await self.fetch_data()
        df = self.clean_data()
        self.data = self.add_calculated_fields(df)
        return self.data
    
    def get_last_n_days(self, n: int = 30) -> pd.DataFrame:
        """
        Get the last N days of processed data.
        
        Args:
            n: Number of days to return (default: 30)
            
        Returns:
            DataFrame with last N days of data
            
        Raises:
            ValueError: If no processed data is available
        """
        if self.data is None:
            raise ValueError("No processed data available. Call process() first.")
        
        return self.data.tail(n).copy()
    
    def get_summary_stats(self) -> dict:
        """
        Calculate summary statistics for the stock.
        
        Returns:
            Dictionary containing summary statistics and technical indicators
        """
        if self.data is None:
            raise ValueError("No processed data available. Call process() first.")
        
        df = self.data
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Count FVGs in last 30 days
        fvg_bullish_count = df['fvg_bullish'].tail(30).sum()
        fvg_bearish_count = df['fvg_bearish'].tail(30).sum()
        
        return {
            "symbol": self.symbol,
            "latest_date": latest['date'].strftime('%Y-%m-%d'),
            "latest_close": round(latest['close'], 2),
            "high_52w": round(df['high'].max(), 2),
            "low_52w": round(df['low'].min(), 2),
            "avg_close": round(df['close'].mean(), 2),
            "avg_volume": int(df['volume'].mean()),
            "volatility": round(latest['volatility'], 6),
            "volatility_annualized": round(latest['volatility_annualized'], 4),
            "total_return": round(
                (df.iloc[-1]['close'] - df.iloc[0]['close']) / df.iloc[0]['close'] * 100, 2
            ),
            "avg_daily_return": round(df['daily_return'].mean() * 100, 4),
            # Technical Indicators
            "technical": {
                "trend": latest.get('trend', 'Neutral'),
                "trend_strength": round(latest.get('trend_strength', 0), 2),
                "rsi": round(latest.get('rsi', 50), 2),
                "rsi_signal": "Overbought" if latest.get('rsi', 50) > 70 else "Oversold" if latest.get('rsi', 50) < 30 else "Neutral",
                "macd": round(latest.get('macd', 0), 2),
                "macd_signal": round(latest.get('macd_signal', 0), 2),
                "macd_histogram": round(latest.get('macd_histogram', 0), 2),
                "macd_trend": "Bullish" if latest.get('macd', 0) > latest.get('macd_signal', 0) else "Bearish",
                "bollinger": {
                    "upper": round(latest.get('bb_upper', 0), 2),
                    "middle": round(latest.get('bb_middle', 0), 2),
                    "lower": round(latest.get('bb_lower', 0), 2),
                    "position": round(latest.get('bb_position', 0.5) * 100, 1),
                    "width": round(latest.get('bb_width', 0) * 100, 2)
                },
                "atr": round(latest.get('atr', 0), 2),
                "support": round(latest.get('support', 0), 2),
                "resistance": round(latest.get('resistance', 0), 2),
                "volume_ratio": round(latest.get('volume_ratio', 1), 2),
                "fair_value_gaps": {
                    "bullish_fvg_30d": int(fvg_bullish_count),
                    "bearish_fvg_30d": int(fvg_bearish_count),
                    "current_position": "Above FVG" if latest.get('fvg_bullish', 0) else "Below FVG" if latest.get('fvg_bearish', 0) else "No Active FVG"
                }
            },
            "moving_averages": {
                "ma_7": round(latest.get('ma_7', 0), 2),
                "ma_20": round(latest.get('ma_20', 0), 2),
                "ma_50": round(latest.get('ma_50', 0), 2),
                "ma_200": round(latest.get('ma_200', 0), 2),
                "price_vs_ma7": "Above" if latest['close'] > latest.get('ma_7', 0) else "Below",
                "price_vs_ma20": "Above" if latest['close'] > latest.get('ma_20', 0) else "Below",
                "price_vs_ma50": "Above" if latest['close'] > latest.get('ma_50', 0) else "Below",
                "price_vs_ma200": "Above" if latest['close'] > latest.get('ma_200', 0) else "Below"
            }
        }


async def fetch_and_process_stock(symbol: str) -> Tuple[pd.DataFrame, dict]:
    """
    Convenience function to fetch and process stock data.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Tuple of (processed DataFrame, summary statistics dict)
    """
    fetcher = StockDataFetcher(symbol)
    data = await fetcher.process()
    summary = fetcher.get_summary_stats()
    return data, summary


def compare_stocks(df1: pd.DataFrame, df2: pd.DataFrame, 
                   symbol1: str, symbol2: str) -> dict:
    """
    Compare two stocks based on various metrics.
    
    Args:
        df1: Processed data for first stock
        df2: Processed data for second stock
        symbol1: Symbol of first stock
        symbol2: Symbol of second stock
        
    Returns:
        Dictionary containing comparison metrics
    """
    # Align data by date for correlation calculation
    merged = pd.merge(
        df1[['date', 'close', 'daily_return']].rename(
            columns={'close': 'close_1', 'daily_return': 'return_1'}
        ),
        df2[['date', 'close', 'daily_return']].rename(
            columns={'close': 'close_2', 'daily_return': 'return_2'}
        ),
        on='date',
        how='inner'
    )
    
    # Calculate correlation
    correlation = merged['return_1'].corr(merged['return_2'])
    
    return {
        "symbol1": symbol1,
        "symbol2": symbol2,
        "comparison_period_days": len(merged),
        "metrics": {
            symbol1: {
                "avg_return": round(df1['daily_return'].mean() * 100, 4),
                "volatility": round(df1['volatility'].iloc[-1], 6),
                "total_return": round(
                    (df1.iloc[-1]['close'] - df1.iloc[0]['close']) / df1.iloc[0]['close'] * 100, 2
                )
            },
            symbol2: {
                "avg_return": round(df2['daily_return'].mean() * 100, 4),
                "volatility": round(df2['volatility'].iloc[-1], 6),
                "total_return": round(
                    (df2.iloc[-1]['close'] - df2.iloc[0]['close']) / df2.iloc[0]['close'] * 100, 2
                )
            }
        },
        "correlation": round(correlation, 4) if not np.isnan(correlation) else None,
        "correlation_interpretation": _interpret_correlation(correlation)
    }


def _interpret_correlation(corr: float) -> str:
    """Interpret correlation coefficient value."""
    if np.isnan(corr):
        return "Unable to calculate"
    elif corr >= 0.7:
        return "Strong positive correlation"
    elif corr >= 0.3:
        return "Moderate positive correlation"
    elif corr >= -0.3:
        return "Weak or no correlation"
    elif corr >= -0.7:
        return "Moderate negative correlation"
    else:
        return "Strong negative correlation"
