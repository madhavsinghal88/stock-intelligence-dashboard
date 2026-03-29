"""
Utility Functions Module

This module contains utility functions for stock data calculations,
including the custom Stock Health Score metric.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from functools import lru_cache
from datetime import datetime, timedelta

from config import SECTOR_MAPPING, STANDARD_SECTORS, SECTOR_COLORS, SECTOR_ICONS


def calculate_health_score(
    avg_return: float,
    volatility: float,
    trend_strength: float,
    price_vs_52w_high: float
) -> Dict[str, Any]:
    """
    Calculate a custom Stock Health Score based on multiple factors.
    
    The Health Score is a composite metric (0-100) that considers:
    - Return Performance (25%): Higher average returns = better score
    - Volatility (25%): Lower volatility = better score (stability)
    - Trend Strength (25%): Stronger upward trend = better score
    - Price Position (25%): Closer to 52-week high = better score
    
    Args:
        avg_return: Average daily return (as decimal, e.g., 0.001 for 0.1%)
        volatility: Rolling volatility (standard deviation of returns)
        trend_strength: Ratio of short-term MA to long-term MA
        price_vs_52w_high: Current price as percentage of 52-week high
    
    Returns:
        Dictionary containing health score and component breakdown
    """
    # Return Score (0-25)
    # Normalize: -2% to +2% daily return maps to 0-25
    return_normalized = (avg_return + 0.02) / 0.04  # Shift and scale
    return_score = max(0, min(25, return_normalized * 25))
    
    # Volatility Score (0-25)
    # Lower volatility is better. Typical range: 0.005 to 0.05
    # Inverse scoring: high volatility = low score
    vol_normalized = 1 - min(volatility / 0.05, 1)  # Cap at 5% daily vol
    volatility_score = max(0, min(25, vol_normalized * 25))
    
    # Trend Score (0-25)
    # trend_strength > 1 means short-term MA > long-term MA (uptrend)
    # Range typically 0.9 to 1.1
    trend_normalized = (trend_strength - 0.9) / 0.2  # Map 0.9-1.1 to 0-1
    trend_score = max(0, min(25, trend_normalized * 25))
    
    # Price Position Score (0-25)
    # How close to 52-week high (as percentage)
    position_score = max(0, min(25, price_vs_52w_high * 0.25))
    
    # Total Health Score
    total_score = return_score + volatility_score + trend_score + position_score
    
    # Determine health category
    if total_score >= 80:
        category = "Excellent"
        description = "Strong performer with low risk and positive momentum"
    elif total_score >= 60:
        category = "Good"
        description = "Solid performance with acceptable risk levels"
    elif total_score >= 40:
        category = "Fair"
        description = "Average performance, monitor for improvements"
    elif total_score >= 20:
        category = "Poor"
        description = "Underperforming with elevated risk factors"
    else:
        category = "Critical"
        description = "Significant concerns across multiple metrics"
    
    return {
        "total_score": round(total_score, 2),
        "category": category,
        "description": description,
        "components": {
            "return_score": round(return_score, 2),
            "volatility_score": round(volatility_score, 2),
            "trend_score": round(trend_score, 2),
            "position_score": round(position_score, 2)
        },
        "max_possible": 100
    }


def calculate_health_score_from_df(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate health score directly from a processed stock DataFrame.
    
    Args:
        df: Processed stock data with calculated fields
        
    Returns:
        Health score dictionary
    """
    if df.empty:
        return {"error": "No data available for health score calculation"}
    
    latest = df.iloc[-1]
    
    # Average return over the period
    avg_return = df['daily_return'].mean()
    
    # Latest volatility
    volatility = latest['volatility'] if not np.isnan(latest['volatility']) else 0.02
    
    # Trend strength: MA7 / MA20 ratio
    if latest['ma_20'] > 0:
        trend_strength = latest['ma_7'] / latest['ma_20']
    else:
        trend_strength = 1.0
    
    # Price position relative to 52-week high
    if latest['high_52w'] > 0:
        price_vs_52w_high = (latest['close'] / latest['high_52w']) * 100
    else:
        price_vs_52w_high = 50.0
    
    return calculate_health_score(
        avg_return=avg_return,
        volatility=volatility,
        trend_strength=trend_strength,
        price_vs_52w_high=price_vs_52w_high
    )


def format_currency(value: float, currency: str = "INR") -> str:
    """
    Format a number as currency string.
    
    Args:
        value: Numeric value to format
        currency: Currency code (default: INR)
        
    Returns:
        Formatted currency string
    """
    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    symbol = symbols.get(currency, "$")
    
    if value >= 10000000:  # 1 Crore
        return f"{symbol}{value/10000000:.2f} Cr"
    elif value >= 100000:  # 1 Lakh
        return f"{symbol}{value/100000:.2f} L"
    else:
        return f"{symbol}{value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a decimal value as percentage string.
    
    Args:
        value: Decimal value (e.g., 0.05 for 5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    """
    Calculate Compound Annual Growth Rate.
    
    Args:
        initial_value: Starting value
        final_value: Ending value
        years: Number of years
        
    Returns:
        CAGR as decimal
    """
    if initial_value <= 0 or years <= 0:
        return 0.0
    return (final_value / initial_value) ** (1 / years) - 1


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.05
) -> float:
    """
    Calculate the Sharpe Ratio for a series of returns.
    
    Args:
        returns: Series of daily returns
        risk_free_rate: Annual risk-free rate (default: 5%)
        
    Returns:
        Annualized Sharpe Ratio
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    
    # Convert annual risk-free rate to daily
    daily_rf = (1 + risk_free_rate) ** (1/252) - 1
    
    excess_returns = returns - daily_rf
    
    # Annualize the Sharpe ratio
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    
    return round(sharpe, 4)


def get_market_status() -> Dict[str, Any]:
    """
    Get current market status (simplified - based on time).
    
    Returns:
        Dictionary with market status information
    """
    now = datetime.now()
    
    # Indian market hours: 9:15 AM - 3:30 PM IST (Monday-Friday)
    # This is a simplified check
    is_weekday = now.weekday() < 5
    
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if is_weekday and market_open <= now <= market_close:
        status = "open"
        message = "Indian market is currently open"
    else:
        status = "closed"
        if not is_weekday:
            message = "Market is closed (Weekend)"
        elif now < market_open:
            message = "Market opens at 9:15 AM IST"
        else:
            message = "Market closed at 3:30 PM IST"
    
    return {
        "status": status,
        "message": message,
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "IST"
    }


def df_to_json_safe(df: pd.DataFrame) -> list:
    """
    Convert DataFrame to JSON-serializable list of dictionaries.
    
    Handles datetime and NaN values properly.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        List of dictionaries
    """
    # Convert datetime columns to strings
    df_copy = df.copy()
    
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
    
    # Replace NaN with None
    df_copy = df_copy.replace({np.nan: None})
    
    # Convert to records
    return df_copy.to_dict(orient='records')


# Predefined list of supported stock symbols - NIFTY 50 Stocks
SUPPORTED_STOCKS = {
    # Financial Services - Banks
    "HDFCBANK.NS": {
        "name": "HDFC Bank Limited",
        "sector": "Banking",
        "exchange": "NSE"
    },
    "ICICIBANK.NS": {
        "name": "ICICI Bank Limited",
        "sector": "Banking",
        "exchange": "NSE"
    },
    "SBIN.NS": {
        "name": "State Bank of India",
        "sector": "Banking",
        "exchange": "NSE"
    },
    "KOTAKBANK.NS": {
        "name": "Kotak Mahindra Bank",
        "sector": "Banking",
        "exchange": "NSE"
    },
    "AXISBANK.NS": {
        "name": "Axis Bank Limited",
        "sector": "Banking",
        "exchange": "NSE"
    },
    "INDUSINDBK.NS": {
        "name": "IndusInd Bank Limited",
        "sector": "Banking",
        "exchange": "NSE"
    },
    
    # Financial Services - Insurance & NBFC
    "BAJFINANCE.NS": {
        "name": "Bajaj Finance Limited",
        "sector": "Financial Services",
        "exchange": "NSE"
    },
    "BAJAJFINSV.NS": {
        "name": "Bajaj Finserv Limited",
        "sector": "Financial Services",
        "exchange": "NSE"
    },
    "HDFCLIFE.NS": {
        "name": "HDFC Life Insurance",
        "sector": "Insurance",
        "exchange": "NSE"
    },
    "SBILIFE.NS": {
        "name": "SBI Life Insurance",
        "sector": "Insurance",
        "exchange": "NSE"
    },
    
    # Information Technology
    "TCS.NS": {
        "name": "Tata Consultancy Services",
        "sector": "Technology",
        "exchange": "NSE"
    },
    "INFY.NS": {
        "name": "Infosys Limited",
        "sector": "Technology",
        "exchange": "NSE"
    },
    "HCLTECH.NS": {
        "name": "HCL Technologies",
        "sector": "Technology",
        "exchange": "NSE"
    },
    "WIPRO.NS": {
        "name": "Wipro Limited",
        "sector": "Technology",
        "exchange": "NSE"
    },
    "TECHM.NS": {
        "name": "Tech Mahindra Limited",
        "sector": "Technology",
        "exchange": "NSE"
    },
    "LTIM.NS": {
        "name": "LTIMindtree Limited",
        "sector": "Technology",
        "exchange": "NSE"
    },
    
    # Energy & Oil & Gas
    "RELIANCE.NS": {
        "name": "Reliance Industries Limited",
        "sector": "Energy",
        "exchange": "NSE"
    },
    "ONGC.NS": {
        "name": "Oil & Natural Gas Corporation",
        "sector": "Oil & Gas",
        "exchange": "NSE"
    },
    "NTPC.NS": {
        "name": "NTPC Limited",
        "sector": "Utilities",
        "exchange": "NSE"
    },
    "POWERGRID.NS": {
        "name": "Power Grid Corporation",
        "sector": "Utilities",
        "exchange": "NSE"
    },
    "ADANIGREEN.NS": {
        "name": "Adani Green Energy",
        "sector": "Renewable Energy",
        "exchange": "NSE"
    },
    "COALINDIA.NS": {
        "name": "Coal India Limited",
        "sector": "Mining",
        "exchange": "NSE"
    },
    
    # Consumer Defensive (FMCG)
    "HINDUNILVR.NS": {
        "name": "Hindustan Unilever Limited",
        "sector": "Consumer Defensive",
        "exchange": "NSE"
    },
    "ITC.NS": {
        "name": "ITC Limited",
        "sector": "Consumer Defensive",
        "exchange": "NSE"
    },
    "NESTLEIND.NS": {
        "name": "Nestle India Limited",
        "sector": "Consumer Defensive",
        "exchange": "NSE"
    },
    "BRITANNIA.NS": {
        "name": "Britannia Industries",
        "sector": "Consumer Defensive",
        "exchange": "NSE"
    },
    "TATACONSUM.NS": {
        "name": "Tata Consumer Products",
        "sector": "Consumer Defensive",
        "exchange": "NSE"
    },
    
    # Automotive
    "TMCV.NS": {
        "name": "Tata Motors Limited",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    "MARUTI.NS": {
        "name": "Maruti Suzuki India",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    "M&M.NS": {
        "name": "Mahindra & Mahindra",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    "BAJAJ-AUTO.NS": {
        "name": "Bajaj Auto Limited",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    "HEROMOTOCO.NS": {
        "name": "Hero MotoCorp Limited",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    "EICHERMOT.NS": {
        "name": "Eicher Motors Limited",
        "sector": "Automotive",
        "exchange": "NSE"
    },
    
    # Pharmaceuticals & Healthcare
    "SUNPHARMA.NS": {
        "name": "Sun Pharmaceutical",
        "sector": "Pharmaceuticals",
        "exchange": "NSE"
    },
    "DRREDDY.NS": {
        "name": "Dr. Reddy's Laboratories",
        "sector": "Pharmaceuticals",
        "exchange": "NSE"
    },
    "CIPLA.NS": {
        "name": "Cipla Limited",
        "sector": "Pharmaceuticals",
        "exchange": "NSE"
    },
    "DIVISLAB.NS": {
        "name": "Divi's Laboratories",
        "sector": "Pharmaceuticals",
        "exchange": "NSE"
    },
    "APOLLOHOSP.NS": {
        "name": "Apollo Hospitals",
        "sector": "Healthcare",
        "exchange": "NSE"
    },
    
    # Industrials & Infrastructure
    "LT.NS": {
        "name": "Larsen & Toubro Limited",
        "sector": "Industrials",
        "exchange": "NSE"
    },
    "ADANIENT.NS": {
        "name": "Adani Enterprises",
        "sector": "Industrials",
        "exchange": "NSE"
    },
    "ADANIPORTS.NS": {
        "name": "Adani Ports & SEZ",
        "sector": "Industrials",
        "exchange": "NSE"
    },
    "ULTRACEMCO.NS": {
        "name": "UltraTech Cement",
        "sector": "Construction",
        "exchange": "NSE"
    },
    "GRASIM.NS": {
        "name": "Grasim Industries",
        "sector": "Industrials",
        "exchange": "NSE"
    },
    "SHREECEM.NS": {
        "name": "Shree Cement Limited",
        "sector": "Construction",
        "exchange": "NSE"
    },
    
    # Metals & Mining
    "TATASTEEL.NS": {
        "name": "Tata Steel Limited",
        "sector": "Basic Materials",
        "exchange": "NSE"
    },
    "JSWSTEEL.NS": {
        "name": "JSW Steel Limited",
        "sector": "Basic Materials",
        "exchange": "NSE"
    },
    "HINDALCO.NS": {
        "name": "Hindalco Industries",
        "sector": "Basic Materials",
        "exchange": "NSE"
    },
    
    # Telecommunications
    "BHARTIARTL.NS": {
        "name": "Bharti Airtel Limited",
        "sector": "Telecommunications",
        "exchange": "NSE"
    },
    
    # Consumer Cyclical (Retail, etc.)
    "TITAN.NS": {
        "name": "Titan Company Limited",
        "sector": "Consumer Cyclical",
        "exchange": "NSE"
    },
    "ASIANPAINT.NS": {
        "name": "Asian Paints Limited",
        "sector": "Consumer Cyclical",
        "exchange": "NSE"
    },
    
    # Real Estate
    "DLF.NS": {
        "name": "DLF Limited",
        "sector": "Real Estate",
        "exchange": "NSE"
    },
    
    # Conglomerate
    "BPCL.NS": {
        "name": "Bharat Petroleum",
        "sector": "Oil & Gas",
        "exchange": "NSE"
    },
    "WIPRO.NS": {
        "name": "Wipro Limited",
        "sector": "Technology",
        "exchange": "NSE"
    }
}


def get_supported_companies() -> list:
    """
    Get list of supported companies with their details.
    
    Returns:
        List of company dictionaries
    """
    return [
        {
            "symbol": symbol,
            **details
        }
        for symbol, details in SUPPORTED_STOCKS.items()
    ]


def validate_symbol(symbol: str) -> bool:
    """
    Validate if a symbol is in the supported list.
    
    Args:
        symbol: Stock symbol to validate
        
    Returns:
        True if valid, False otherwise
    """
    return symbol.upper() in SUPPORTED_STOCKS


# Exchange code to readable name mapping
EXCHANGE_MAP = {
    # Indian Exchanges
    "NSI": "NSE",
    "NSE": "NSE",
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NCM": "NASDAQ",
    "BSE": "BSE",
    "BOM": "BSE",
    
    # US Exchanges
    "NYQ": "NYSE",
    "NYSE": "NYSE",
    "NYS": "NYSE",
    "NAS": "NASDAQ",
    "NASDAQ": "NASDAQ",
    "PCX": "NYSE ARCA",
    "ASE": "NYSE American",
    "BTS": "BATS",
    "PNK": "OTC Pink",
    "OTC": "OTC",
    "OTCQB": "OTCQB",
    "OTCQX": "OTCQX",
    
    # European Exchanges
    "GER": "XETRA (Germany)",
    "FRA": "Frankfurt",
    "ETR": "XETRA",
    "LON": "London",
    "LSE": "London",
    "PAR": "Euronext Paris",
    "EPA": "Euronext Paris",
    "AMS": "Euronext Amsterdam",
    "BRU": "Euronext Brussels",
    "MIL": "Milan",
    "STO": "Stockholm",
    "HEL": "Helsinki",
    "CPH": "Copenhagen",
    "OSL": "Oslo",
    "SWX": "Swiss Exchange",
    "VIE": "Vienna",
    "MAD": "Madrid",
    "MCE": "Madrid",
    
    # Asian Exchanges
    "TYO": "Tokyo",
    "JPX": "Tokyo",
    "HKG": "Hong Kong",
    "HKE": "Hong Kong",
    "SHA": "Shanghai",
    "SHH": "Shanghai",
    "SHE": "Shenzhen",
    "SHZ": "Shenzhen",
    "KRX": "Korea",
    "KSC": "Korea",
    "KOE": "Korea",
    "TAI": "Taiwan",
    "TWO": "Taiwan OTC",
    "TPE": "Taiwan",
    "SGX": "Singapore",
    "SES": "Singapore",
    "ASX": "Australia",
    "AX": "Australia",
    "NZE": "New Zealand",
    "JAK": "Jakarta",
    "JKT": "Jakarta",
    "BKK": "Thailand",
    "SET": "Thailand",
    "KLS": "Kuala Lumpur",
    "MYX": "Malaysia",
    
    # Other Exchanges
    "TOR": "Toronto",
    "TSX": "Toronto",
    "TSE": "Toronto",
    "CVE": "TSX Venture",
    "SAO": "Sao Paulo",
    "MEX": "Mexico",
    "SGO": "Santiago",
    "BUE": "Buenos Aires",
    "JSE": "Johannesburg",
    "TAE": "Tel Aviv",
    "IST": "Istanbul",
    "WSE": "Warsaw",
    "ATH": "Athens",
    
    # Crypto/Other
    "CCC": "Cryptocurrency",
    "CCY": "Currency",
}


def get_exchange_name(exchange_code: str) -> str:
    """
    Convert exchange code to readable exchange name.
    
    Args:
        exchange_code: Raw exchange code from Yahoo Finance
        
    Returns:
        Human-readable exchange name
    """
    if not exchange_code:
        return "Unknown"
    
    code = exchange_code.upper()
    return EXCHANGE_MAP.get(code, exchange_code)


def get_country_from_symbol(symbol: str) -> str:
    """
    Determine the country/market from a stock symbol suffix.
    
    Args:
        symbol: Stock symbol (e.g., RELIANCE.NS, BMW.DE)
        
    Returns:
        Country/Market name
    """
    suffix_map = {
        ".NS": "India (NSE)",
        ".BO": "India (BSE)",
        ".DE": "Germany",
        ".L": "UK",
        ".PA": "France",
        ".AS": "Netherlands",
        ".MI": "Italy",
        ".MC": "Spain",
        ".SW": "Switzerland",
        ".ST": "Sweden",
        ".CO": "Denmark",
        ".OL": "Norway",
        ".HE": "Finland",
        ".VI": "Austria",
        ".T": "Japan",
        ".HK": "Hong Kong",
        ".SS": "China (Shanghai)",
        ".SZ": "China (Shenzhen)",
        ".KS": "South Korea",
        ".KQ": "South Korea (KOSDAQ)",
        ".TW": "Taiwan",
        ".TWO": "Taiwan (OTC)",
        ".SI": "Singapore",
        ".AX": "Australia",
        ".NZ": "New Zealand",
        ".JK": "Indonesia",
        ".BK": "Thailand",
        ".KL": "Malaysia",
        ".TO": "Canada (TSX)",
        ".V": "Canada (Venture)",
        ".SA": "Brazil",
        ".MX": "Mexico",
        ".SN": "Chile",
        ".BA": "Argentina",
        ".JO": "South Africa",
        ".TA": "Israel",
        ".IS": "Turkey",
    }
    
    symbol_upper = symbol.upper()
    for suffix, country in suffix_map.items():
        if symbol_upper.endswith(suffix.upper()):
            return country
    
    # No suffix usually means US
    if "." not in symbol:
        return "USA"
    
    return "Unknown"


def format_market_cap(value: Optional[float]) -> str:
    """
    Format market cap to human readable string.
    
    Args:
        value: Market cap value
        
    Returns:
        Formatted string (e.g., "1.5T", "250B", "50M")
    """
    if value is None:
        return "N/A"
    
    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(int(value))


# ==========================================
# Sector Normalization Functions
# ==========================================

def normalize_sector(sector: Optional[str]) -> str:
    """
    Normalize a sector name to a standardized name.
    
    This function handles various sector name variations from different
    data sources (Yahoo Finance, etc.) and maps them to consistent names.
    
    Args:
        sector: Raw sector name from data source
        
    Returns:
        Standardized sector name
        
    Examples:
        >>> normalize_sector("Information Technology")
        "Technology"
        >>> normalize_sector("Banks - Regional")
        "Banking"
        >>> normalize_sector(None)
        "Unknown"
    """
    if not sector:
        return "Unknown"
    
    # Normalize to lowercase for matching
    sector_lower = sector.lower().strip()
    
    # Direct lookup in mapping
    if sector_lower in SECTOR_MAPPING:
        return SECTOR_MAPPING[sector_lower]
    
    # Check if already a standard sector (case-insensitive)
    for std_sector in STANDARD_SECTORS:
        if sector_lower == std_sector.lower():
            return std_sector
    
    # Fuzzy matching: check if any mapping key is contained in the sector
    for key, value in SECTOR_MAPPING.items():
        if key in sector_lower or sector_lower in key:
            return value
    
    # If sector contains certain keywords, categorize accordingly
    keyword_mapping = {
        "bank": "Banking",
        "insurance": "Insurance",
        "pharma": "Pharmaceuticals",
        "drug": "Pharmaceuticals",
        "biotech": "Biotechnology",
        "software": "Technology",
        "internet": "Technology",
        "semiconductor": "Technology",
        "oil": "Oil & Gas",
        "gas": "Oil & Gas",
        "energy": "Energy",
        "utility": "Utilities",
        "electric": "Utilities",
        "power": "Utilities",
        "real estate": "Real Estate",
        "reit": "Real Estate",
        "retail": "Retail",
        "auto": "Automotive",
        "vehicle": "Automotive",
        "telecom": "Telecommunications",
        "wireless": "Telecommunications",
        "media": "Media & Entertainment",
        "entertainment": "Media & Entertainment",
        "healthcare": "Healthcare",
        "hospital": "Healthcare",
        "medical": "Healthcare",
        "food": "Food & Beverage",
        "beverage": "Food & Beverage",
        "restaurant": "Travel & Leisure",
        "hotel": "Travel & Leisure",
        "travel": "Travel & Leisure",
        "airline": "Transportation",
        "shipping": "Transportation",
        "logistics": "Logistics",
        "freight": "Logistics",
        "construction": "Construction",
        "building": "Construction",
        "cement": "Construction",
        "mining": "Mining",
        "metal": "Basic Materials",
        "steel": "Basic Materials",
        "chemical": "Basic Materials",
        "agriculture": "Agriculture",
        "farm": "Agriculture",
        "aerospace": "Aerospace & Defense",
        "defense": "Aerospace & Defense",
        "defence": "Aerospace & Defense",
        "conglomerate": "Conglomerate",
        "diversified": "Conglomerate",
    }
    
    for keyword, mapped_sector in keyword_mapping.items():
        if keyword in sector_lower:
            return mapped_sector
    
    # Return original if no mapping found (capitalized)
    return sector.title() if sector else "Unknown"


def get_sector_color(sector: str) -> str:
    """
    Get the display color for a sector.
    
    Args:
        sector: Sector name (will be normalized if needed)
        
    Returns:
        Hex color code
    """
    normalized = normalize_sector(sector)
    return SECTOR_COLORS.get(normalized, SECTOR_COLORS.get("Unknown", "#616161"))


def get_sector_icon(sector: str) -> str:
    """
    Get the display icon/emoji for a sector.
    
    Args:
        sector: Sector name (will be normalized if needed)
        
    Returns:
        Emoji/unicode icon
    """
    normalized = normalize_sector(sector)
    return SECTOR_ICONS.get(normalized, SECTOR_ICONS.get("Unknown", "❓"))


def get_all_sectors() -> List[Dict[str, str]]:
    """
    Get list of all standardized sectors with their colors and icons.
    
    Returns:
        List of sector dictionaries with name, color, and icon
    """
    return [
        {
            "name": sector,
            "color": SECTOR_COLORS.get(sector, "#616161"),
            "icon": SECTOR_ICONS.get(sector, "❓")
        }
        for sector in STANDARD_SECTORS
        if sector != "Unknown"  # Exclude Unknown from main list
    ]


def get_sector_info(sector: str) -> Dict[str, str]:
    """
    Get complete sector information including normalized name, color, and icon.
    
    Args:
        sector: Raw sector name
        
    Returns:
        Dictionary with normalized name, color, and icon
    """
    normalized = normalize_sector(sector)
    return {
        "name": normalized,
        "original": sector,
        "color": SECTOR_COLORS.get(normalized, "#616161"),
        "icon": SECTOR_ICONS.get(normalized, "❓")
    }
