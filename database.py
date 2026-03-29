"""
Database Module

This module handles SQLite database operations for caching stock data
to reduce API calls and improve response times.
"""

import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from contextlib import contextmanager
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database file path
# On Vercel serverless, only /tmp is writable
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/stock_data.db"
else:
    DB_PATH = "stock_data.db"

# Cache duration in hours
CACHE_DURATION_HOURS = 1


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        SQLite connection object
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """
    Initialize the database with required tables.
    
    Creates tables for:
    - stock_data: Cached processed stock data
    - cache_metadata: Cache timestamps and metadata
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table for storing processed stock data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                daily_return REAL,
                ma_7 REAL,
                ma_20 REAL,
                high_52w REAL,
                low_52w REAL,
                volatility REAL,
                volatility_annualized REAL,
                price_change REAL,
                price_change_pct REAL,
                UNIQUE(symbol, date)
            )
        """)
        
        # Table for cache metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                symbol TEXT PRIMARY KEY,
                last_updated TEXT NOT NULL,
                record_count INTEGER,
                data_start_date TEXT,
                data_end_date TEXT
            )
        """)
        
        # Table for summary statistics cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary_cache (
                symbol TEXT PRIMARY KEY,
                summary_json TEXT NOT NULL,
                health_score_json TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_symbol 
            ON stock_data(symbol)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_date 
            ON stock_data(date)
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")


def is_cache_valid(symbol: str) -> bool:
    """
    Check if cached data for a symbol is still valid.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        True if cache is valid, False otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_updated FROM cache_metadata WHERE symbol = ?",
            (symbol.upper(),)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        last_updated = datetime.fromisoformat(result['last_updated'])
        cache_age = datetime.now() - last_updated
        
        return cache_age < timedelta(hours=CACHE_DURATION_HOURS)


def save_stock_data(symbol: str, df: pd.DataFrame):
    """
    Save processed stock data to the database.
    
    Args:
        symbol: Stock symbol
        df: Processed DataFrame to save
    """
    symbol = symbol.upper()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Delete existing data for this symbol
        cursor.execute("DELETE FROM stock_data WHERE symbol = ?", (symbol,))
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            records.append((
                symbol,
                row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date'],
                row.get('open'),
                row.get('high'),
                row.get('low'),
                row.get('close'),
                row.get('volume'),
                row.get('daily_return'),
                row.get('ma_7'),
                row.get('ma_20'),
                row.get('high_52w'),
                row.get('low_52w'),
                row.get('volatility'),
                row.get('volatility_annualized'),
                row.get('price_change'),
                row.get('price_change_pct')
            ))
        
        # Bulk insert
        cursor.executemany("""
            INSERT INTO stock_data 
            (symbol, date, open, high, low, close, volume, daily_return, 
             ma_7, ma_20, high_52w, low_52w, volatility, volatility_annualized,
             price_change, price_change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        
        # Update cache metadata
        cursor.execute("""
            INSERT OR REPLACE INTO cache_metadata 
            (symbol, last_updated, record_count, data_start_date, data_end_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            symbol,
            datetime.now().isoformat(),
            len(df),
            df['date'].min().strftime('%Y-%m-%d') if hasattr(df['date'].min(), 'strftime') else str(df['date'].min()),
            df['date'].max().strftime('%Y-%m-%d') if hasattr(df['date'].max(), 'strftime') else str(df['date'].max())
        ))
        
        conn.commit()
        logger.info(f"Saved {len(records)} records for {symbol}")


def load_stock_data(symbol: str) -> Optional[pd.DataFrame]:
    """
    Load cached stock data from the database.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        DataFrame with cached data or None if not found
    """
    symbol = symbol.upper()
    
    with get_db_connection() as conn:
        query = """
            SELECT date, open, high, low, close, volume, daily_return,
                   ma_7, ma_20, high_52w, low_52w, volatility, 
                   volatility_annualized, price_change, price_change_pct
            FROM stock_data 
            WHERE symbol = ?
            ORDER BY date
        """
        
        df = pd.read_sql_query(query, conn, params=(symbol,))
        
        if df.empty:
            return None
        
        # Convert date string to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        return df


def save_summary_cache(symbol: str, summary: dict, health_score: dict):
    """
    Save summary statistics to cache.
    
    Args:
        symbol: Stock symbol
        summary: Summary statistics dictionary
        health_score: Health score dictionary
    """
    symbol = symbol.upper()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO summary_cache 
            (symbol, summary_json, health_score_json, last_updated)
            VALUES (?, ?, ?, ?)
        """, (
            symbol,
            json.dumps(summary),
            json.dumps(health_score),
            datetime.now().isoformat()
        ))
        conn.commit()


def load_summary_cache(symbol: str) -> Optional[Tuple[dict, dict]]:
    """
    Load cached summary statistics.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Tuple of (summary, health_score) or None if not found/expired
    """
    symbol = symbol.upper()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT summary_json, health_score_json, last_updated FROM summary_cache WHERE symbol = ?",
            (symbol,)
        )
        result = cursor.fetchone()
        
        if not result:
            return None
        
        # Check if cache is valid
        last_updated = datetime.fromisoformat(result['last_updated'])
        if datetime.now() - last_updated > timedelta(hours=CACHE_DURATION_HOURS):
            return None
        
        return (
            json.loads(result['summary_json']),
            json.loads(result['health_score_json'])
        )


def get_cache_info() -> list:
    """
    Get information about cached data.
    
    Returns:
        List of dictionaries with cache information
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, last_updated, record_count, 
                   data_start_date, data_end_date
            FROM cache_metadata
            ORDER BY last_updated DESC
        """)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]


def clear_cache(symbol: Optional[str] = None):
    """
    Clear cached data.
    
    Args:
        symbol: If provided, clear only this symbol's cache.
                If None, clear all cached data.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if symbol:
            symbol = symbol.upper()
            cursor.execute("DELETE FROM stock_data WHERE symbol = ?", (symbol,))
            cursor.execute("DELETE FROM cache_metadata WHERE symbol = ?", (symbol,))
            cursor.execute("DELETE FROM summary_cache WHERE symbol = ?", (symbol,))
            logger.info(f"Cleared cache for {symbol}")
        else:
            cursor.execute("DELETE FROM stock_data")
            cursor.execute("DELETE FROM cache_metadata")
            cursor.execute("DELETE FROM summary_cache")
            logger.info("Cleared all cached data")
        
        conn.commit()


# Initialize database on module import
init_database()
