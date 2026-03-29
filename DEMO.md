# Stock Data Intelligence Dashboard - Complete Demonstration

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Features Breakdown](#features-breakdown)
6. [Tech Stack](#tech-stack)
7. [Interview Questions & Answers](#interview-questions--answers)
8. [Code Examples](#code-examples)
9. [Deployment](#deployment)

---

## Project Overview

A comprehensive stock market data analysis platform that:
- Fetches real-time data from Yahoo Finance API
- Processes data with 20+ technical indicators
- Calculates custom "Stock Health Score" (0-100)
- Supports 52 Nifty 50 stocks + global search
- Provides NSE/BSE exchange comparison
- **Interactive Technical Analysis with Candlestick Charts**
- **RSI, MACD, Bollinger Bands visualizations**
- **Fair Value Gap (FVG) detection**
- **Support/Resistance levels**
- Interactive Chart.js dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Search    │  │   Charts    │  │   Filters   │              │
│  │   Results   │  │  (Chart.js) │  │  (Sectors)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (Port 8007)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   REST API  │  │  Caching    │  │   Health    │              │
│  │  Endpoints │  │  Layer       │  │   Score      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌───────────────────┐  ┌───────────────────┐
        │   Yahoo Finance   │  │     SQLite        │
        │      API          │  │     Database     │
        │  (yfinance)       │  │   (Caching)      │
        └───────────────────┘  └───────────────────┘
```

### Component Flow

```
User Request → FastAPI → Check Cache → [Cache Hit] → Return
                              │
                              ▼
                    [Cache Miss] → yfinance API → Process Data → Save Cache → Return
```

---

## Database Schema

### SQLite: `stock_data.db`

#### Table 1: `stock_cache`
```sql
CREATE TABLE stock_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    data TEXT NOT NULL,           -- JSON serialized DataFrame
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_count INTEGER
);
```

**Sample Data:**
| symbol | last_updated | record_count |
|--------|--------------|--------------|
| TCS.NS | 2026-03-29 10:30:00 | 252 |
| INFY.NS | 2026-03-29 10:31:00 | 252 |

#### Table 2: `summary_cache`
```sql
CREATE TABLE summary_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,        -- JSON serialized summary dict
    health_score TEXT NOT NULL,   -- JSON serialized health score
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table 3: `search_cache`
```sql
CREATE TABLE search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    results TEXT NOT NULL,        -- JSON serialized search results
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

### Base URL: `http://localhost:8007`

### 1. Companies Endpoint

#### `GET /companies`
Get list of all supported Nifty 50 stocks.

**Response:**
```json
[
  {
    "symbol": "TCS.NS",
    "name": "Tata Consultancy Services",
    "sector": "Technology",
    "exchange": "NSE"
  },
  {
    "symbol": "HDFCBANK.NS",
    "name": "HDFC Bank Limited",
    "sector": "Banking",
    "exchange": "NSE"
  }
]
```

---

### 2. Search Endpoint

#### `GET /search?q={query}`
Search stocks globally via Yahoo Finance.

**Parameters:**
- `q` (required): Search query (1-50 chars)
- `sector` (optional): Filter by sector

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "type": "EQUITY",
    "score": 1000000,
    "sector": "Technology",
    "sector_color": "#00d4ff"
  }
]
```

**Example:**
```bash
curl "http://localhost:8007/search?q=tesla"
```

---

### 3. Stock Data Endpoint

#### `GET /data/{symbol}?days=30`
Get historical stock data with calculated indicators.

**Parameters:**
- `symbol` (required): Stock ticker (e.g., `TCS.NS`, `AAPL`)
- `days` (optional): Days of data (1-365, default: 30)

**Response:**
```json
{
  "symbol": "TCS.NS",
  "company_name": "Tata Consultancy Services",
  "data_points": 30,
  "period": "Last 30 days",
  "data": [
    {
      "date": "2026-03-01",
      "open": 3850.50,
      "high": 3890.00,
      "low": 3840.25,
      "close": 3885.75,
      "volume": 2450000,
      "daily_return": 0.0092,
      "ma_7": 3865.30,
      "ma_20": 3820.15,
      "volatility": 0.0156
    }
  ]
}
```

---

### 4. Stock Summary Endpoint

#### `GET /summary/{symbol}`
Get comprehensive summary with Health Score.

**Response:**
```json
{
  "symbol": "TCS.NS",
  "company_name": "Tata Consultancy Services",
  "latest_date": "2026-03-29",
  "latest_close": 3895.50,
  "high_52w": 4250.00,
  "low_52w": 3200.00,
  "avg_close": 3725.00,
  "avg_volume": 2100000,
  "volatility": 0.0189,
  "volatility_annualized": 0.3002,
  "total_return": 15.5,
  "avg_daily_return": 0.065,
  "health_score": {
    "total_score": 78.5,
    "category": "Good",
    "description": "Solid performance with acceptable risk levels",
    "components": {
      "return_score": 20.5,
      "volatility_score": 18.2,
      "trend_score": 20.0,
      "position_score": 19.8
    },
    "max_possible": 100
  }
}
```

---

### 5. Stock Info Endpoint

#### `GET /stock/{symbol}/info`
Get detailed stock information.

**Response:**
```json
{
  "symbol": "TCS.NS",
  "name": "Tata Consultancy Services",
  "sector": "Technology",
  "sector_color": "#00d4ff",
  "sector_icon": "💻",
  "industry": "Information Technology Services",
  "exchange": "NSE",
  "country": "India (NSE)",
  "currency": "INR",
  "market_cap": 1425000000000,
  "market_cap_formatted": "1.42T",
  "current_price": 3895.50,
  "pe_ratio": 26.5,
  "dividend_yield": 1.8,
  "beta": 0.85,
  "fifty_two_week_high": 4250.00,
  "fifty_two_week_low": 3200.00
}
```

---

### 6. Exchange Comparison Endpoint

#### `GET /stock/{symbol}/exchanges`
Get NSE & BSE prices for Indian stocks.

**Response:**
```json
{
  "symbol_base": "RELIANCE",
  "exchanges": [
    {
      "exchange": "NSE",
      "exchange_full": "National Stock Exchange",
      "symbol": "RELIANCE.NS",
      "price": 1348.10,
      "previous_close": 1413.10,
      "change": -65.0,
      "change_percent": -4.6,
      "currency": "INR"
    },
    {
      "exchange": "BSE",
      "exchange_full": "Bombay Stock Exchange",
      "symbol": "RELIANCE.BO",
      "price": 1348.25,
      "change_percent": -4.55,
      "currency": "INR"
    }
  ],
  "is_indian_stock": true,
  "price_difference": -0.15,
  "price_difference_pct": -0.01
}
```

---

### 7. Sectors Endpoints

#### `GET /sectors`
Get all standardized sectors.

**Response:**
```json
[
  {"name": "Technology", "color": "#00d4ff", "icon": "💻"},
  {"name": "Banking", "color": "#2E7D32", "icon": "🏦"},
  {"name": "Financial Services", "color": "#4CAF50", "icon": "💰"},
  {"name": "Energy", "color": "#F44336", "icon": "⚡"}
]
```

#### `GET /sectors/{sector_name}`
Get info about a specific sector.

**Response:**
```json
{
  "input": "Information Technology",
  "normalized": "Technology",
  "color": "#00d4ff",
  "icon": "💻",
  "is_valid": true
}
```

---

### 8. Stock Comparison Endpoint

#### `GET /compare?symbol1={s1}&symbol2={s2}`
Compare two stocks.

**Response:**
```json
{
  "symbol1": "TCS.NS",
  "symbol2": "INFY.NS",
  "comparison_period_days": 250,
  "metrics": {
    "TCS.NS": {
      "avg_return": 0.065,
      "volatility": 0.0189,
      "total_return": 15.5
    },
    "INFY.NS": {
      "avg_return": 0.052,
      "volatility": 0.0225,
      "total_return": 12.3
    }
  },
  "correlation": 0.7823,
  "correlation_interpretation": "Strong positive correlation"
}
```

---

### 9. Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/market-status` | GET | Indian market open/closed status |
| `/cache/info` | GET | Cached symbols info |
| `/cache/{symbol}` | DELETE | Clear cache for symbol |
| `/cache` | DELETE | Clear all cache |
| `/health` | GET | API health check |

---

## Features Breakdown

### 1. Technical Indicators

| Indicator | Formula | Purpose |
|----------|---------|---------|
| Daily Return | `(Close - Open) / Open` | Measure daily performance |
| 7-Day MA | `Rolling mean(Close, 7)` | Short-term trend |
| 20-Day MA | `Rolling mean(Close, 20)` | Medium-term trend |
| 50-Day MA | `Rolling mean(Close, 50)` | Medium-term trend |
| 200-Day MA | `Rolling mean(Close, 200)` | Long-term trend |
| 52-Week High | `Max(High, 252 days)` | Resistance level |
| 52-Week Low | `Min(Low, 252 days)` | Support level |
| Volatility | `StdDev(Daily Returns, 20)` | Risk measure |
| Annualized Volatility | `Volatility × √252` | Yearly risk |
| **RSI (14)** | `100 - (100 / (1 + RS))` | Overbought/Oversold (70/30) |
| **MACD** | `EMA(12) - EMA(26)` | Trend momentum |
| **MACD Signal** | `EMA(MACD, 9)` | Signal line crossover |
| **Bollinger Bands** | `MA20 ± 2×StdDev` | Volatility channels |
| **ATR (14)** | `Avg(True Range)` | Average price movement |
| **Fair Value Gap** | `Bullish/Bearish gaps` | Liquidity zones |
| **Trend Detection** | `Price vs MA50` | Bullish/Bearish/Neutral |

### 2. Stock Health Score Algorithm

```
Health Score (0-100) = Return Score + Volatility Score + Trend Score + Position Score
```

| Component | Weight | Calculation |
|-----------|--------|------------|
| Return Score | 25 | Maps -2% to +2% → 0-25 |
| Volatility Score | 25 | Lower volatility = higher score |
| Trend Score | 25 | MA7/MA20 ratio → 0.9-1.1 range |
| Position Score | 25 | Close vs 52-week high |

**Categories:**
- Excellent: 80-100
- Good: 60-79
- Fair: 40-59
- Poor: 20-39
- Critical: 0-19

### 3. Sector Normalization

300+ variations mapped to 32 standardized sectors:
- "Information Technology", "IT", "Software" → "Technology"
- "Banks - Regional", "Private Banks" → "Banking"
- "Auto - Manufacturers", "Two Wheelers" → "Automotive"

### 4. Exchange Mapping

70+ global exchanges mapped:
- "NSI" → "NSE"
- "BOM" → "BSE"
- "NMS" → "NASDAQ"
- "NYQ" → "NYSE"
- "GER" → "XETRA (Germany)"

---

## Technical Analysis Features

### Dashboard Tabs
1. **Overview Tab** - Basic stock info, health score, line chart
2. **Compare Tab** - Compare two stocks
3. **Technical Analysis Tab** - Full technical analysis with:

### Candlestick Chart
- OHLC (Open, High, Low, Close) visualization
- Color-coded bars (green = bullish, red = bearish)
- Interactive tooltips with price data

### RSI (Relative Strength Index)
- 14-day RSI calculation
- Overbought (>70) / Oversold (<30) zones
- Neutral zone (30-70)
- Separate chart panel

### MACD (Moving Average Convergence Divergence)
- MACD Line (12-day EMA - 26-day EMA)
- Signal Line (9-day EMA of MACD)
- Histogram (MACD - Signal)
- Crossover signals visualization

### Bollinger Bands
- Upper Band (MA20 + 2×StdDev)
- Middle Band (20-day MA)
- Lower Band (MA20 - 2×StdDev)
- Band Width % (volatility indicator)
- Price Position within bands

### Moving Averages Status
- MA7, MA20, MA50, MA200
- Price vs each MA (Above/Below)
- Trend confirmation

### Fair Value Gap (FVG)
- Bullish FVG detection
- Bearish FVG detection
- 30-day FVG count
- Current FVG position

### Support & Resistance
- Dynamic support level (20-day low)
- Dynamic resistance level (20-day high)
- ATR for stop-loss calculation

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | FastAPI | REST API framework |
| Data Fetch | yfinance | Yahoo Finance API |
| Processing | Pandas, NumPy | Data manipulation |
| Database | SQLite | Caching layer |
| Frontend | HTML, CSS, JS | User interface |
| Charts | Chart.js | Data visualization |
| Server | Uvicorn | ASGI server |

---

## Interview Questions & Answers

### Section 1: Architecture & Design

**Q1: Explain your project architecture.**
> **A:** The project follows a layered architecture:
> - **Frontend Layer:** Single-page application with HTML/CSS/JavaScript, using Chart.js for visualizations
> - **API Layer:** FastAPI handles REST endpoints with async support
> - **Business Logic Layer:** Data processing, Health Score calculation, sector normalization
> - **Data Layer:** SQLite for caching, yfinance for external data
> 
> Request flow: User → FastAPI → Cache Check → [Hit] Return / [Miss] Fetch from yfinance → Process → Cache → Return

---

**Q2: Why did you choose FastAPI over Flask/Django?**
> **A:** 
> - **Async Support:** FastAPI handles concurrent requests efficiently with `async/await`
> - **Auto-documentation:** Swagger UI auto-generated from type hints
> - **Pydantic Integration:** Built-in request/response validation
> - **Performance:** Near Flask speed, comparable to Node.js
> - **Type Safety:** Full IDE support with type hints

---

**Q3: How does caching improve performance?**
> **A:** 
> - Reduces API calls to Yahoo Finance (rate limited)
> - SQLite queries are fast (< 10ms)
> - Cache TTL: 1 hour (configurable)
> - Implementation: Check `is_cache_valid(symbol)` → Return cached or fetch fresh
> - Cache invalidation: Manual via `/cache/{symbol}` DELETE endpoint

---

**Q4: Explain the caching strategy used.**
> **A:**
> - **Cache Storage:** SQLite database
> - **Cache Duration:** 1 hour (`CACHE_DURATION_HOURS = 1`)
> - **Cache Check:** `is_cache_valid(symbol)` compares `last_updated` with current time
> - **Two-tier Caching:**
>   - Stock data cache (raw DataFrame)
>   - Summary cache (aggregated stats + health score)
> - **Manual Invalidation:** Available via API endpoints

---

### Section 2: Technical Indicators

**Q5: How do you calculate Stock Health Score?**
> **A:** The Health Score (0-100) is a composite of four components:
>
> ```python
> # 1. Return Score (0-25): Based on average daily returns
> return_score = max(0, min(25, (avg_return + 0.02) / 0.04 * 25))
> 
> # 2. Volatility Score (0-25): Inverse - lower is better
> vol_score = max(0, min(25, (1 - min(volatility / 0.05, 1)) * 25))
> 
> # 3. Trend Score (0-25): MA7/MA20 ratio
> trend_score = max(0, min(25, (ma_ratio - 0.9) / 0.2 * 25))
> 
> # 4. Position Score (0-25): Close vs 52-week high
> position_score = max(0, min(25, price_vs_52w_high * 0.25))
> 
> total_score = return_score + vol_score + trend_score + position_score
> ```

---

**Q6: Why use moving averages in stock analysis?**
> **A:**
> - **MA7:** Short-term trend indicator, reacts quickly to price changes
> - **MA20:** Medium-term trend, filters out daily noise
> - **Trend Detection:** MA7 > MA20 = Uptrend (bullish)
> - **Support/Resistance:** Prices often bounce off MAs
> - **Crossover Strategy:** MA7 crossing MA20 = Signal

---

**Q7: What is volatility and why is it important?**
> **A:**
> - **Definition:** Standard deviation of daily returns, measures price fluctuation
> - **Calculation:** `Volatility = StdDev(Daily Returns, 20)`
> - **Annualized:** `Volatility × √252` (252 trading days)
> - **Importance:**
>   - Higher volatility = Higher risk
>   - Lower volatility = More stable
> - **Use Case:** Health Score penalizes high volatility

---

**Q8: How do you calculate correlation between two stocks?**
> **A:**
> ```python
> # Merge data by date
> merged = pd.merge(df1[['date', 'daily_return']], 
>                   df2[['date', 'daily_return']], on='date')
> 
> # Calculate Pearson correlation
> correlation = merged['daily_return_x'].corr(merged['daily_return_y'])
> 
> # Interpretation:
> # 0.7 to 1.0 = Strong positive
> # 0.3 to 0.7 = Moderate positive
> # -0.3 to 0.3 = Weak/None
> # -0.7 to -0.3 = Moderate negative
> # -1.0 to -0.7 = Strong negative
> ```

---

### Section 3: Data Handling

**Q9: How do you handle missing data in stock prices?**
> **A:**
> ```python
> # Forward fill for price data (use previous day's value)
> for col in ['open', 'high', 'low', 'close']:
>     df[col] = df[col].ffill()
> 
> # Fill volume with 0 if missing (no trading)
> df['volume'] = df['volume'].fillna(0)
> 
> # Drop rows with critical missing data
> df = df.dropna(subset=['open', 'high', 'low', 'close'])
> ```

---

**Q10: Why do you normalize sector names?**
> **A:**
> - Yahoo Finance returns inconsistent sector names:
>   - "Information Technology"
>   - "IT Services"
>   - "Software - Infrastructure"
> - Solution: 300+ mappings to 32 standardized names
> ```python
> def normalize_sector(sector):
>     sector_lower = sector.lower().strip()
>     if sector_lower in SECTOR_MAPPING:
>         return SECTOR_MAPPING[sector_lower]
>     # Fuzzy matching fallback...
> ```

---

### Section 4: API Design

**Q11: How did you design the REST API?**
> **A:**
> - **Resource-based URLs:** `/stocks/{symbol}`, `/companies`, `/sectors`
> - **HTTP Methods:** GET for retrieval, DELETE for cache management
> - **Query Parameters:** Filtering (`?days=30`, `?q=search`)
> - **Response Codes:** 200 (success), 404 (not found), 500 (server error)
> - **Consistent Format:** All responses include `symbol` field

---

**Q12: How do you handle errors gracefully?**
> **A:**
> ```python
> try:
>     data = await fetch_stock_data(symbol)
> except ValueError as e:
>     raise HTTPException(status_code=404, detail={
>         "error": "NotFound",
>         "message": str(e),
>         "symbol": symbol
>     })
> except Exception as e:
>     logger.error(f"Error: {str(e)}")
>     raise HTTPException(status_code=500, detail={
>         "error": "ServerError",
>         "message": "Failed to process request"
>     })
> ```

---

**Q13: What are the benefits of async/await in FastAPI?**
> **A:**
> - **Concurrent Requests:** Handle multiple requests simultaneously
> - **Non-blocking I/O:** While waiting for Yahoo Finance, handle other requests
> - **Resource Efficiency:** Fewer threads needed
> ```python
> async def get_stock_data(symbol: str):
>     # Await multiple fetches concurrently
>     info, summary, data = await asyncio.gather(
>         fetch_info(symbol),
>         fetch_summary(symbol),
>         fetch_data(symbol)
>     )
> ```

---

### Section 5: Database

**Q14: Why SQLite for caching instead of Redis/MongoDB?**
> **A:**
> - **Simplicity:** Zero configuration, file-based
> - **Built-in Python:** No separate server needed
> - **ACID Compliant:** Safe for concurrent access
> - **Performance:** Sufficient for this scale (< 100 symbols)
> - **Trade-offs:**
>   - Redis: Better for high-traffic, distributed systems
>   - MongoDB: Better for flexible schemas, horizontal scaling

---

**Q15: How is data stored in SQLite?**
> **A:**
> - **DataFrame Storage:** JSON serialized as TEXT
> - **Schema:**
> ```sql
> stock_cache: symbol, data (JSON), last_updated, record_count
> summary_cache: symbol, summary (JSON), health_score (JSON), last_updated
> ```
> - **Serialization:** `df.to_json()` and `pd.read_json(df_str)`

---

### Section 6: Yahoo Finance Integration

**Q16: How do you fetch data from Yahoo Finance?**
> **A:**
> ```python
> import yfinance as yf
> 
> # Single stock
> ticker = yf.Ticker("TCS.NS")
> data = ticker.history(period="1y")
> 
> # Stock info
> info = ticker.info
> price = info.get('regularMarketPrice')
> 
> # Search
> search = yf.Search("tesla", max_results=10)
> results = search.quotes
> ```

---

**Q17: What are the challenges with Yahoo Finance API?**
> **A:**
> - **Rate Limiting:** Can't make too many requests
> - **Symbol Variations:** Same stock different symbols
>   - NSE: `TCS.NS`
>   - BSE: `TCS.BO`
> - **Data Gaps:** Missing days (weekends, holidays)
> - **Exchange Codes:** Raw codes like "NSI" need mapping
> - **Solutions:** Caching, symbol mapping, forward-fill gaps

---

**Q18: Why do Indian stocks use .NS and .BO suffixes?**
> **A:**
> - **.NS:** National Stock Exchange (NSE)
> - **.BO:** Bombay Stock Exchange (BSE)
> - **Why:** Yahoo Finance needs exchange identifier
> - **Price Difference:** Same stock can have different prices on NSE vs BSE
> - **Implementation:** Try both exchanges for Indian stocks

---

### Section 7: Frontend

**Q19: How does Chart.js integration work?**
> **A:**
> ```javascript
> const ctx = document.getElementById('priceChart').getContext('2d');
> 
> new Chart(ctx, {
>     type: 'line',
>     data: {
>         labels: dates,
>         datasets: [
>             { label: 'Close Price', data: prices, borderColor: '#00d4ff' },
>             { label: '7-Day MA', data: ma7, borderDash: [5, 5] }
>         ]
>     },
>     options: {
>         responsive: true,
>         plugins: { legend: { labels: { color: '#888' } } }
>     }
> });
> ```

---

**Q20: How do you handle real-time search with debouncing?**
> **A:**
> ```javascript
> let searchTimer = null;
> 
> searchInput.addEventListener('input', (e) => {
>     clearTimeout(searchTimer);  // Cancel previous
>     
>     searchTimer = setTimeout(() => {
>         performSearch(e.target.value);  // Execute after 300ms
>     }, 300);
> });
> ```
> - **Purpose:** Avoid API spam while typing
> - **Delay:** 300ms is standard for user experience

---

### Section 8: Technical Analysis

**Q21: How do you calculate RSI (Relative Strength Index)?**
> **A:**
> - **Formula:** `RSI = 100 - (100 / (1 + RS))`
> - **RS (Relative Strength):** `Avg Gain / Avg Loss` over 14 periods
> - **Interpretation:**
>   - RSI > 70 = Overbought (potential sell signal)
>   - RSI < 30 = Oversold (potential buy signal)
>   - RSI = 50 = Neutral
> ```python
> delta = df['close'].diff()
> gain = delta.where(delta > 0, 0)
> loss = -delta.where(delta < 0, 0)
> avg_gain = gain.rolling(window=14).mean()
> avg_loss = loss.rolling(window=14).mean()
> rs = avg_gain / avg_loss
> rsi = 100 - (100 / (1 + rs))
> ```

---

**Q22: Explain MACD (Moving Average Convergence Divergence).**
> **A:**
> - **MACD Line:** `EMA(12) - EMA(26)` - Shows short vs long term momentum
> - **Signal Line:** `EMA(9)` of MACD - Smoothed trend line
> - **Histogram:** `MACD - Signal` - Shows momentum shift
> - **Signals:**
>   - MACD crosses above Signal = Bullish
>   - MACD crosses below Signal = Bearish
>   - Histogram growing = Increasing momentum
> ```python
> exp1 = df['close'].ewm(span=12).mean()
> exp2 = df['close'].ewm(span=26).mean()
> macd = exp1 - exp2
> signal = macd.ewm(span=9).mean()
> histogram = macd - signal
> ```

---

**Q23: What are Bollinger Bands?**
> **A:**
> - **Middle Band:** 20-day Simple Moving Average
> - **Upper Band:** `MA20 + (2 × Standard Deviation)`
> - **Lower Band:** `MA20 - (2 × Standard Deviation)`
> - **Width:** `(Upper - Lower) / Middle × 100` - Measures volatility
> - **Signals:**
>   - Price touching upper band = Potentially overbought
>   - Price touching lower band = Potentially oversold
>   - Squeeze (bands close together) = Low volatility, breakout coming

---

**Q24: What is Fair Value Gap (FVG)?**
> **A:**
> - **Definition:** Gaps in price action where institutional orders were filled
> - **Bullish FVG:** Current candle's low > Previous candle's high (by gap)
> - **Bearish FVG:** Current candle's high < Previous candle's low (by gap)
> - **Trading Strategy:**
>   - Price returning to FVG often finds liquidity
>   - FVG acts as support/resistance zones
> ```python
> df['fvg_bullish'] = (df['low'] > df['high'].shift(2)) & (df['low'].shift(1) > df['high'].shift(2))
> df['fvg_bearish'] = (df['high'] < df['low'].shift(2)) & (df['high'].shift(1) < df['low'].shift(2))
> ```

---

**Q25: How do you detect trend direction?**
> **A:**
> - **Simple Method:** Price vs MA50
>   - Price > MA50 = Bullish
>   - Price < MA50 = Bearish
> - **Trend Strength:** `|Price - MA50| / MA50 × 100`
> - **Multiple MAs Confirmation:**
>   - MA7 > MA20 > MA50 > MA200 = Strong Uptrend
>   - MA7 < MA20 < MA50 < MA200 = Strong Downtrend
> ```python
> df['trend'] = np.where(df['close'] > df['ma_50'], 'Bullish',
>                         np.where(df['close'] < df['ma_50'], 'Bearish', 'Neutral'))
> df['trend_strength'] = abs(df['close'] - df['ma_50']) / df['ma_50'] * 100
> ```

---

**Q26: What is ATR (Average True Range)?**
> **A:**
> - **Purpose:** Measures market volatility
> - **True Range:** Max of:
>   - Current High - Current Low
>   - |Current High - Previous Close|
>   - |Current Low - Previous Close|
> - **Calculation:** 14-period ATR = Simple moving average of True Range
> - **Use Cases:**
>   - Stop-loss placement: Entry - (2 × ATR)
>   - Position sizing based on volatility

---

### Section 9: Testing & Deployment

**Q27: How would you test this application?**
> **A:**
> ```python
> # Unit Tests
> def test_health_score_calculation():
>     score = calculate_health_score(0.001, 0.015, 1.02, 85)
>     assert 60 <= score['total_score'] <= 80
> 
> def test_sector_normalization():
>     assert normalize_sector("Information Technology") == "Technology"
>     assert normalize_sector("Banks") == "Banking"
> 
> def test_rsi_calculation():
>     rsi = calculate_rsi(df['close'])
>     assert 0 <= rsi.iloc[-1] <= 100
> 
> # API Tests
> def test_get_stock_data():
>     response = client.get("/data/TCS.NS?days=30")
>     assert response.status_code == 200
>     assert 'data' in response.json()
> ```

---

**Q28: How would you deploy this to production?**
> **A:**
> 1. **Environment:** Python 3.9+, pip
> 2. **Process Manager:** Gunicorn with Uvicorn workers
>    ```bash
>    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
>    ```
> 3. **Reverse Proxy:** Nginx for static files + load balancing
> 4. **Caching:** Consider Redis for multi-instance deployment
> 5. **Monitoring:** Prometheus + Grafana for metrics
> 6. **CI/CD:** GitHub Actions for automated testing/deployment

---

**Q29: What improvements would you make?**
> **A:**
> - **Real-time Data:** WebSocket for live prices
> - **More Indicators:** VWAP, Ichimoku, Fibonacci retracement
> - **Machine Learning:** Price prediction models
> - **User Authentication:** Portfolio tracking
> - **Caching:** Redis for distributed deployment
> - **Rate Limiting:** Protect against abuse
> - **Docker:** Containerized deployment

---

## Code Examples

### 1. Health Score Calculation

```python
def calculate_health_score(avg_return, volatility, trend_strength, price_vs_52w_high):
    # Return Score (0-25)
    return_score = max(0, min(25, (avg_return + 0.02) / 0.04 * 25))
    
    # Volatility Score (0-25) - inverse
    vol_score = max(0, min(25, (1 - min(volatility / 0.05, 1)) * 25))
    
    # Trend Score (0-25)
    trend_score = max(0, min(25, (trend_strength - 0.9) / 0.2 * 25))
    
    # Position Score (0-25)
    position_score = max(0, min(25, price_vs_52w_high * 0.25))
    
    return {
        'total_score': return_score + vol_score + trend_score + position_score,
        'components': {
            'return_score': return_score,
            'volatility_score': vol_score,
            'trend_score': trend_score,
            'position_score': position_score
        }
    }
```

### 2. Caching Implementation

```python
def is_cache_valid(symbol, hours=1):
    query = "SELECT last_updated FROM stock_cache WHERE symbol = ?"
    result = db.execute(query, (symbol,)).fetchone()
    
    if result:
        cached_time = datetime.fromisoformat(result[0])
        age = datetime.now() - cached_time
        return age.total_seconds() < (hours * 3600)
    return False

def get_or_fetch(symbol):
    if is_cache_valid(symbol):
        return load_from_cache(symbol)
    else:
        data = fetch_from_yfinance(symbol)
        save_to_cache(symbol, data)
        return data
```

### 3. Stock Comparison

```python
def compare_stocks(df1, df2):
    merged = pd.merge(
        df1[['date', 'daily_return']],
        df2[['date', 'daily_return']],
        on='date'
    )
    
    correlation = merged['daily_return_x'].corr(merged['daily_return_y'])
    
    return {
        'correlation': round(correlation, 4),
        'interpretation': get_correlation_interpretation(correlation)
    }
```

---

## Deployment

### Quick Start

```bash
# Clone repository
git clone https://github.com/madhavsinghal88/stock-intelligence-dashboard.git
cd stock-intelligence-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
# OR
uvicorn main:app --reload --host 0.0.0.0 --port 8007

# Access
# Dashboard: http://localhost:8007
# API Docs:  http://localhost:8007/docs
```

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8007
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
```

---

## Summary

This project demonstrates:
- ✅ Full-stack development (FastAPI + HTML/CSS/JS)
- ✅ External API integration (Yahoo Finance)
- ✅ Data processing & analysis (Pandas, NumPy)
- ✅ Database management (SQLite caching)
- ✅ Technical analysis (Indicators, Health Score)
- ✅ REST API design
- ✅ Interactive frontend (Chart.js)
- ✅ Production-ready code structure

---

**Author:** Madhav Singhal  
**Version:** 1.0.0  
**License:** MIT
