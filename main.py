"""
Stock Data Intelligence Dashboard - Main Application

A FastAPI-based backend for fetching, processing, and analyzing stock market data.
Provides RESTful API endpoints for stock data, summaries, and comparisons.

Author: Stock Intelligence Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List, Optional
import logging
from pathlib import Path
import yfinance as yf

# Local imports
from data_fetcher import StockDataFetcher, compare_stocks
from utils import (
    get_supported_companies,
    validate_symbol,
    calculate_health_score_from_df,
    df_to_json_safe,
    get_market_status,
    get_exchange_name,
    get_country_from_symbol,
    format_market_cap,
    normalize_sector,
    get_sector_color,
    get_sector_icon,
    get_all_sectors,
    get_sector_info,
    SUPPORTED_STOCKS
)
from database import (
    is_cache_valid,
    save_stock_data,
    load_stock_data,
    save_summary_cache,
    load_summary_cache,
    get_cache_info,
    clear_cache
)
from models import (
    CompanyInfo,
    StockDataResponse,
    StockSummary,
    StockComparison,
    ErrorResponse,
    HealthScore,
    CacheInfo,
    MarketStatus,
    SearchResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Stock Data Intelligence Dashboard",
    description="""
    A comprehensive API for stock market data analysis and intelligence.
    
    ## Features
    - Fetch and process stock data from Yahoo Finance
    - Calculate technical indicators (Moving Averages, Volatility)
    - Custom Stock Health Score metric
    - Compare multiple stocks
    - SQLite caching for improved performance
    
    ## Supported Stocks
    NSE listed stocks including INFY, TCS, RELIANCE, HDFCBANK, and more.
    """,
    version="1.0.0",
    contact={
        "name": "Stock Intelligence API",
        "email": "api@stockintelligence.example.com"
    },
    license_info={
        "name": "MIT License"
    }
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directory for resolving paths
BASE_DIR = Path(__file__).parent.resolve()

# Mount static files directory
static_path = BASE_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Pre-load index.html content at import time for reliable serving on Vercel
# Log file structure in Vercel environment for debugging
if os.environ.get("VERCEL"):
    logger.info("Listing all files in /var/task:")
    for root, dirs, files in os.walk("/var/task"):
        for name in files:
            if not name.endswith('.pyc') and '.venv' not in root and '.vercel' not in root:
                logger.info(f"File found: {os.path.join(root, name)}")

_INDEX_HTML_CONTENT = None
_possible_html_paths = [
    BASE_DIR / "static" / "index.html",
    Path.cwd() / "static" / "index.html",
    Path("/var/task") / "static" / "index.html",
    Path("/var/task") / "index.html",
    BASE_DIR.parent / "static" / "index.html",  # When running from api/
]

for _p in _possible_html_paths:
    if _p.exists():
        _INDEX_HTML_CONTENT = _p.read_text(encoding="utf-8")
        logger.info(f"Loaded index.html from: {_p}")
        break

if _INDEX_HTML_CONTENT is None:
    logger.warning(f"index.html not found in any path. BASE_DIR={BASE_DIR}, CWD={Path.cwd()}")



# ============================================================================
# Helper Functions
# ============================================================================

async def get_or_fetch_stock_data(symbol: str):
    """
    Get stock data from cache or fetch fresh data.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Tuple of (DataFrame, was_cached)
    """
    symbol = symbol.upper()
    
    # Check cache first
    if is_cache_valid(symbol):
        logger.info(f"Using cached data for {symbol}")
        df = load_stock_data(symbol)
        if df is not None:
            return df, True
    
    # Fetch fresh data
    logger.info(f"Fetching fresh data for {symbol}")
    fetcher = StockDataFetcher(symbol)
    df = await fetcher.process()
    
    # Save to cache
    save_stock_data(symbol, df)
    
    return df, False


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Serve the main dashboard HTML page."""
    if _INDEX_HTML_CONTENT:
        return HTMLResponse(content=_INDEX_HTML_CONTENT)
    
    # Fallback if template doesn't exist
    return HTMLResponse(content="""
    <html>
        <head>
            <title>Stock Intelligence Dashboard</title>
        </head>
        <body>
            <h1>Stock Data Intelligence Dashboard</h1>
            <p>Welcome to the Stock Intelligence API.</p>
            <p>Visit <a href="/docs">/docs</a> for API documentation.</p>
        </body>
    </html>
    """)


@app.get(
    "/companies",
    response_model=List[CompanyInfo],
    summary="Get List of Companies",
    description="Returns a list of all supported stock symbols with company information.",
    tags=["Companies"]
)
async def get_companies():
    """
    Get the list of supported companies.
    
    Returns predefined list of NSE stock symbols with:
    - Company name
    - Sector
    - Exchange information
    """
    return get_supported_companies()


@app.get(
    "/search",
    response_model=List[SearchResult],
    summary="Search Stocks",
    description="Search for any stock symbol from Yahoo Finance.",
    tags=["Search"]
)
async def search_stocks(
    q: str = Query(..., min_length=1, max_length=50, description="Search query (company name or symbol)"),
    sector: Optional[str] = Query(None, description="Filter by sector (standardized name)")
):
    """
    Search for stocks by name or symbol using Yahoo Finance.
    
    Args:
        q: Search query string
        sector: Optional sector filter (uses standardized sector names)
    
    Returns:
        List of matching stocks with symbol, name, exchange, sector, and type
    """
    try:
        # Use yfinance search
        search = yf.Search(q, max_results=20)
        
        results = []
        
        # Get quotes (stocks)
        if hasattr(search, 'quotes') and search.quotes:
            for quote in search.quotes:
                raw_exchange = quote.get('exchange', 'Unknown')
                exchange_name = get_exchange_name(raw_exchange)
                
                # Get sector info - may need to fetch from ticker
                raw_sector = quote.get('sector', '')
                
                # Normalize the sector
                normalized_sector = normalize_sector(raw_sector) if raw_sector else None
                
                # If sector filter is applied, skip non-matching results
                if sector:
                    if not normalized_sector or normalize_sector(sector).lower() != normalized_sector.lower():
                        continue
                
                results.append(SearchResult(
                    symbol=quote.get('symbol', ''),
                    name=quote.get('shortname') or quote.get('longname') or quote.get('symbol', ''),
                    exchange=exchange_name,
                    type=quote.get('quoteType', 'EQUITY'),
                    score=quote.get('score', 0),
                    sector=normalized_sector,
                    sector_color=get_sector_color(normalized_sector) if normalized_sector else None
                ))
        
        # Sort by score (relevance)
        results.sort(key=lambda x: x.score or 0, reverse=True)
        
        return results
        
    except Exception as e:
        logger.error(f"Search error for '{q}': {str(e)}")
        # Return empty list instead of error for better UX
        return []


@app.get(
    "/stock/{symbol}/info",
    summary="Get Stock Info",
    description="Get basic information about any stock from Yahoo Finance.",
    tags=["Search"]
)
async def get_stock_info(symbol: str):
    """
    Get basic information about a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT, RELIANCE.NS)
    
    Returns:
        Stock information including name, sector, market cap, etc.
    """
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if not info or info.get('regularMarketPrice') is None:
            # Fallback: check if it's in our supported list
            supported = SUPPORTED_STOCKS.get(symbol.upper())
            if supported:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "NotFound",
                        "message": f"Stock '{symbol}' is in our list but data temporarily unavailable from Yahoo Finance. Please try again later.",
                        "symbol": symbol.upper()
                    }
                )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFound",
                    "message": f"No data found for symbol '{symbol}'",
                    "symbol": symbol.upper()
                }
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFound",
                    "message": f"No data found for symbol '{symbol}'",
                    "symbol": symbol.upper()
                }
            )
        
        # Get readable exchange name
        raw_exchange = info.get('exchange', '')
        exchange_name = get_exchange_name(raw_exchange)
        
        # Get country/market
        country = get_country_from_symbol(symbol.upper())
        
        # Format market cap
        market_cap_raw = info.get('marketCap')
        market_cap_formatted = format_market_cap(market_cap_raw)
        
        # Normalize sector and industry
        raw_sector = info.get('sector', '')
        raw_industry = info.get('industry', '')
        sector_info = get_sector_info(raw_sector)
        
        return {
            "symbol": symbol.upper(),
            "name": info.get('shortName') or info.get('longName') or symbol.upper(),
            "sector": sector_info['name'],
            "sector_raw": raw_sector if raw_sector else None,
            "sector_color": sector_info['color'],
            "sector_icon": sector_info['icon'],
            "industry": raw_industry if raw_industry else 'N/A',
            "exchange": exchange_name,
            "exchange_code": raw_exchange,
            "country": country,
            "currency": info.get('currency', 'N/A'),
            "market_cap": market_cap_raw,
            "market_cap_formatted": market_cap_formatted,
            "current_price": info.get('regularMarketPrice'),
            "previous_close": info.get('previousClose'),
            "day_high": info.get('dayHigh'),
            "day_low": info.get('dayLow'),
            "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
            "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
            "volume": info.get('volume'),
            "avg_volume": info.get('averageVolume'),
            "pe_ratio": info.get('trailingPE'),
            "dividend_yield": info.get('dividendYield'),
            "beta": info.get('beta'),
            "description": info.get('longBusinessSummary', '')[:500] if info.get('longBusinessSummary') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching info for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ServerError",
                "message": f"Failed to fetch stock info: {str(e)}",
                "symbol": symbol.upper()
            }
        )


@app.get(
    "/stock/{symbol}/exchanges",
    summary="Get Stock Prices from Multiple Exchanges",
    description="Get prices from both NSE and BSE for Indian stocks, or available exchanges for other stocks.",
    tags=["Search"]
)
async def get_stock_exchanges(symbol: str):
    """
    Get stock prices from multiple exchanges (NSE/BSE for Indian stocks).
    
    Args:
        symbol: Base stock symbol (e.g., RELIANCE, INFY, TCS)
    
    Returns:
        Prices from available exchanges
    """
    symbol_base = symbol.upper().replace('.NS', '').replace('.BO', '')
    
    exchanges = []
    
    # Try NSE
    try:
        nse_symbol = f"{symbol_base}.NS"
        ticker_nse = yf.Ticker(nse_symbol)
        info_nse = ticker_nse.info
        
        if info_nse and info_nse.get('regularMarketPrice'):
            exchanges.append({
                "exchange": "NSE",
                "exchange_full": "National Stock Exchange",
                "symbol": nse_symbol,
                "price": info_nse.get('regularMarketPrice'),
                "previous_close": info_nse.get('previousClose'),
                "change": round(info_nse.get('regularMarketPrice', 0) - info_nse.get('previousClose', 0), 2),
                "change_percent": round(
                    ((info_nse.get('regularMarketPrice', 0) - info_nse.get('previousClose', 1)) / 
                     info_nse.get('previousClose', 1)) * 100, 2
                ),
                "day_high": info_nse.get('dayHigh'),
                "day_low": info_nse.get('dayLow'),
                "volume": info_nse.get('volume'),
                "currency": "INR"
            })
    except Exception as e:
        logger.debug(f"NSE data not available for {symbol_base}: {e}")
    
    # Try BSE
    try:
        bse_symbol = f"{symbol_base}.BO"
        ticker_bse = yf.Ticker(bse_symbol)
        info_bse = ticker_bse.info
        
        if info_bse and info_bse.get('regularMarketPrice'):
            exchanges.append({
                "exchange": "BSE",
                "exchange_full": "Bombay Stock Exchange",
                "symbol": bse_symbol,
                "price": info_bse.get('regularMarketPrice'),
                "previous_close": info_bse.get('previousClose'),
                "change": round(info_bse.get('regularMarketPrice', 0) - info_bse.get('previousClose', 0), 2),
                "change_percent": round(
                    ((info_bse.get('regularMarketPrice', 0) - info_bse.get('previousClose', 1)) / 
                     info_bse.get('previousClose', 1)) * 100, 2
                ),
                "day_high": info_bse.get('dayHigh'),
                "day_low": info_bse.get('dayLow'),
                "volume": info_bse.get('volume'),
                "currency": "INR"
            })
    except Exception as e:
        logger.debug(f"BSE data not available for {symbol_base}: {e}")
    
    if not exchanges:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NotFound",
                "message": f"No exchange data found for '{symbol_base}'. This may not be an Indian stock.",
                "symbol": symbol_base
            }
        )
    
    # Calculate price difference between exchanges
    price_diff = None
    if len(exchanges) == 2:
        nse_price = exchanges[0]['price']
        bse_price = exchanges[1]['price']
        price_diff = {
            "absolute": round(abs(nse_price - bse_price), 2),
            "percent": round(abs(nse_price - bse_price) / min(nse_price, bse_price) * 100, 4),
            "arbitrage_opportunity": abs(nse_price - bse_price) > 1,  # More than Rs 1 difference
            "higher_exchange": "NSE" if nse_price > bse_price else "BSE"
        }
    
    return {
        "symbol_base": symbol_base,
        "name": exchanges[0].get('name', symbol_base) if exchanges else symbol_base,
        "exchanges": exchanges,
        "price_difference": price_diff,
        "available_exchanges": [e['exchange'] for e in exchanges]
    }


@app.get(
    "/sectors",
    summary="Get All Sectors",
    description="Returns list of all standardized sectors with their colors and icons.",
    tags=["Sectors"]
)
async def get_sectors():
    """
    Get list of all standardized sectors.
    
    Returns:
        List of sectors with name, color, and icon
    """
    return get_all_sectors()


@app.get(
    "/sectors/{sector_name}",
    summary="Get Sector Info",
    description="Get information about a specific sector including standardized name.",
    tags=["Sectors"]
)
async def get_sector_details(sector_name: str):
    """
    Get detailed information about a sector.
    
    Args:
        sector_name: Sector name (will be normalized to standard name)
    
    Returns:
        Sector info with normalized name, color, and icon
    """
    info = get_sector_info(sector_name)
    return {
        "input": sector_name,
        "normalized": info['name'],
        "color": info['color'],
        "icon": info['icon'],
        "is_valid": info['name'] != "Unknown"
    }


@app.get(
    "/data/{symbol}",
    response_model=StockDataResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Stock not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get Stock Data",
    description="Returns the last 30 days of processed stock data for any stock symbol.",
    tags=["Stock Data"]
)
async def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of data to return")
):
    """
    Get processed stock data for any stock symbol from Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., INFY.NS, AAPL, MSFT)
        days: Number of days of data to return (default: 30, max: 365)
    
    Returns:
        Processed stock data including:
        - OHLCV data
        - Daily returns
        - Moving averages
        - Volatility metrics
    """
    symbol = symbol.upper()
    
    try:
        df, was_cached = await get_or_fetch_stock_data(symbol)
        
        # Get last N days
        data = df.tail(days)
        
        # Convert to JSON-safe format
        data_records = df_to_json_safe(data)
        
        # Get company name from predefined list or use symbol
        company_info = SUPPORTED_STOCKS.get(symbol, {})
        company_name = company_info.get("name") if company_info else None
        
        # If not in predefined list, try to get name from yfinance
        if not company_name:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('shortName') or info.get('longName') or symbol
            except:
                company_name = symbol
        
        return StockDataResponse(
            symbol=symbol,
            company_name=company_name,
            data_points=len(data_records),
            period=f"Last {days} days",
            data=data_records
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "DataNotFound",
                "message": str(e),
                "symbol": symbol
            }
        )
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ServerError",
                "message": f"Failed to fetch data: {str(e)}",
                "symbol": symbol
            }
        )


@app.get(
    "/summary/{symbol}",
    response_model=StockSummary,
    responses={
        404: {"model": ErrorResponse, "description": "Stock not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get Stock Summary",
    description="Returns comprehensive summary statistics and health score for any stock.",
    tags=["Stock Data"]
)
async def get_stock_summary(symbol: str):
    """
    Get summary statistics for any stock from Yahoo Finance.
    
    Args:
        symbol: Stock ticker symbol (e.g., INFY.NS, AAPL, MSFT)
    
    Returns:
        Summary including:
        - 52-week high and low
        - Average closing price
        - Volatility metrics
        - Custom Health Score
    """
    symbol = symbol.upper()
    
    try:
        # Check summary cache
        cached = load_summary_cache(symbol)
        if cached:
            summary, health_score = cached
            company_info = SUPPORTED_STOCKS.get(symbol, {})
            company_name = company_info.get("name") if company_info else summary.get("symbol", symbol)
            return StockSummary(
                **summary,
                company_name=company_name,
                health_score=HealthScore(**health_score)
            )
        
        # Fetch fresh data
        df, _ = await get_or_fetch_stock_data(symbol)
        
        # Calculate summary
        fetcher = StockDataFetcher(symbol)
        fetcher.data = df
        summary = fetcher.get_summary_stats()
        
        # Calculate health score
        health_score = calculate_health_score_from_df(df)
        
        # Cache the results
        save_summary_cache(symbol, summary, health_score)
        
        # Get company name
        company_info = SUPPORTED_STOCKS.get(symbol, {})
        company_name = company_info.get("name") if company_info else None
        
        if not company_name:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company_name = info.get('shortName') or info.get('longName') or symbol
            except:
                company_name = symbol
        
        return StockSummary(
            **summary,
            company_name=company_name,
            health_score=HealthScore(**health_score)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "DataNotFound",
                "message": str(e),
                "symbol": symbol
            }
        )
    except Exception as e:
        logger.error(f"Error getting summary for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ServerError",
                "message": f"Failed to calculate summary: {str(e)}",
                "symbol": symbol
            }
        )


@app.get(
    "/compare",
    response_model=StockComparison,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Stock not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Compare Two Stocks",
    description="Compare any two stocks based on returns, volatility, and correlation.",
    tags=["Analysis"]
)
async def compare_two_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol")
):
    """
    Compare any two stocks on various metrics.
    
    Args:
        symbol1: First stock symbol (e.g., AAPL, INFY.NS)
        symbol2: Second stock symbol (e.g., MSFT, TCS.NS)
    
    Returns:
        Comparison including:
        - Average returns for each stock
        - Volatility comparison
        - Price correlation
    """
    symbol1 = symbol1.upper()
    symbol2 = symbol2.upper()
    
    if symbol1 == symbol2:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "InvalidRequest",
                "message": "Cannot compare a stock with itself. Please provide two different symbols."
            }
        )
    
    try:
        # Fetch data for both stocks
        df1, _ = await get_or_fetch_stock_data(symbol1)
        df2, _ = await get_or_fetch_stock_data(symbol2)
        
        # Compare stocks
        comparison = compare_stocks(df1, df2, symbol1, symbol2)
        
        return StockComparison(**comparison)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "DataNotFound",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error comparing {symbol1} and {symbol2}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ServerError",
                "message": f"Failed to compare stocks: {str(e)}"
            }
        )


# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get(
    "/market-status",
    response_model=MarketStatus,
    summary="Get Market Status",
    description="Returns current market status (open/closed) based on IST timezone.",
    tags=["Utilities"]
)
async def market_status():
    """Get current Indian market status."""
    return get_market_status()


@app.get(
    "/cache/info",
    response_model=List[CacheInfo],
    summary="Get Cache Information",
    description="Returns information about cached stock data.",
    tags=["Utilities"]
)
async def cache_info():
    """Get information about cached data."""
    return get_cache_info()


@app.delete(
    "/cache/{symbol}",
    summary="Clear Cache for Symbol",
    description="Clears cached data for a specific symbol.",
    tags=["Utilities"]
)
async def clear_symbol_cache(symbol: str):
    """Clear cache for a specific symbol."""
    symbol = symbol.upper()
    clear_cache(symbol)
    return {"message": f"Cache cleared for {symbol}"}


@app.delete(
    "/cache",
    summary="Clear All Cache",
    description="Clears all cached stock data.",
    tags=["Utilities"]
)
async def clear_all_cache():
    """Clear all cached data."""
    clear_cache()
    return {"message": "All cache cleared"}


@app.get(
    "/health",
    summary="Health Check",
    description="API health check endpoint.",
    tags=["Utilities"]
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Stock Data Intelligence Dashboard",
        "version": "1.0.0"
    }


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Stock Data Intelligence Dashboard...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
