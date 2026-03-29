# Stock Data Intelligence Dashboard

A comprehensive stock market data analysis platform built with FastAPI, providing real-time stock data, technical indicators, and AI-driven insights through a custom Stock Health Score metric.

## Overview

This project is a full-stack stock analysis dashboard that fetches data from Yahoo Finance, processes it with various technical indicators, and presents it through a clean REST API and interactive web dashboard. It's designed with clean architecture principles and is suitable for fintech applications.

## Features

- **Global Stock Search**: Search and analyze any stock worldwide (US, India, Europe, Asia & more)
- **Real-time Stock Data**: Fetch 1 year of historical data from Yahoo Finance
- **Technical Indicators**: 
  - Daily Returns
  - 7-day & 20-day Moving Averages
  - 52-week High/Low
  - Rolling Volatility (20-day window)
  - Annualized Volatility
- **Custom Stock Health Score**: Proprietary metric combining return, volatility, trend, and price position
- **Stock Comparison**: Compare two stocks with correlation analysis
- **Multi-Exchange Support**: 
  - NSE/BSE toggle for Indian stocks with price comparison
  - Proper exchange name display (70+ global exchanges mapped)
  - Country detection from symbol suffix
- **SQLite Caching**: Reduces API calls and improves response times
- **Interactive Dashboard**: Modern, responsive UI with Chart.js visualizations
- **Comprehensive API Documentation**: Auto-generated Swagger/OpenAPI docs

## Project Structure

```
stock-dashboard/
├── main.py              # FastAPI application entry point
├── data_fetcher.py      # Stock data fetching and processing
├── utils.py             # Utility functions and calculations
├── models.py            # Pydantic models for request/response
├── database.py          # SQLite database operations
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── stock_data.db        # SQLite database (auto-created)
├── static/              # Static assets
└── templates/
    └── index.html       # Dashboard frontend
```

## API Endpoints

### Companies & Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/companies` | GET | Get list of popular/predefined stock symbols |
| `/search?q={query}` | GET | Search any stock globally by symbol or name |

### Stock Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/data/{symbol}` | GET | Get processed stock data (default: last 30 days) |
| `/summary/{symbol}` | GET | Get summary statistics with health score |
| `/stock/{symbol}/info` | GET | Get detailed stock info (exchange, country, market cap) |
| `/stock/{symbol}/exchanges` | GET | Get NSE & BSE prices for Indian stocks |
| `/compare` | GET | Compare two stocks (query params: symbol1, symbol2) |

### Utilities

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/market-status` | GET | Get current Indian market status |
| `/cache/info` | GET | Get cache information |
| `/cache/{symbol}` | DELETE | Clear cache for a symbol |
| `/cache` | DELETE | Clear all cached data |
| `/health` | GET | API health check |

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd stock-dashboard
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   # Option 1: Using Python directly
   python main.py
   
   # Option 2: Using uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8007
   ```

5. **Access the application**
   - Dashboard: http://localhost:8007
   - API Documentation: http://localhost:8007/docs
   - Alternative API Docs: http://localhost:8007/redoc

## Sample API Responses

### GET /companies
```json
[
  {
    "symbol": "INFY.NS",
    "name": "Infosys Limited",
    "sector": "Information Technology",
    "exchange": "NSE"
  },
  {
    "symbol": "TCS.NS",
    "name": "Tata Consultancy Services",
    "sector": "Information Technology",
    "exchange": "NSE"
  }
]
```

### GET /summary/INFY.NS
```json
{
  "symbol": "INFY.NS",
  "company_name": "Infosys Limited",
  "latest_date": "2024-01-15",
  "latest_close": 1567.45,
  "high_52w": 1689.90,
  "low_52w": 1215.45,
  "avg_close": 1445.67,
  "avg_volume": 8567890,
  "volatility": 0.015678,
  "volatility_annualized": 0.2489,
  "total_return": 12.45,
  "avg_daily_return": 0.0523,
  "health_score": {
    "total_score": 68.5,
    "category": "Good",
    "description": "Solid performance with acceptable risk levels",
    "components": {
      "return_score": 17.5,
      "volatility_score": 18.2,
      "trend_score": 16.8,
      "position_score": 16.0
    },
    "max_possible": 100
  }
}
```

### GET /compare?symbol1=INFY.NS&symbol2=TCS.NS
```json
{
  "symbol1": "INFY.NS",
  "symbol2": "TCS.NS",
  "comparison_period_days": 250,
  "metrics": {
    "INFY.NS": {
      "avg_return": 0.0523,
      "volatility": 0.015678,
      "total_return": 12.45
    },
    "TCS.NS": {
      "avg_return": 0.0412,
      "volatility": 0.012345,
      "total_return": 8.92
    }
  },
  "correlation": 0.7823,
  "correlation_interpretation": "Strong positive correlation"
}
```

### GET /stock/RELIANCE/exchanges
```json
{
  "symbol_base": "RELIANCE",
  "name": "RELIANCE",
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
      "previous_close": 1412.55,
      "change": -64.3,
      "change_percent": -4.55,
      "currency": "INR"
    }
  ],
  "is_indian_stock": true,
  "price_difference": -0.15,
  "price_difference_pct": -0.01
}
```

### GET /search?q=tesla
```json
[
  {
    "symbol": "TSLA",
    "name": "Tesla, Inc.",
    "exchange": "NASDAQ",
    "type": "Equity",
    "score": 1000000
  },
  {
    "symbol": "TSLA.MX",
    "name": "Tesla, Inc.",
    "exchange": "Mexico",
    "type": "Equity",
    "score": 20120
  }
]
```

## Supported Exchanges

The dashboard maps 70+ global exchange codes to readable names, including:

| Region | Exchanges |
|--------|-----------|
| India | NSE, BSE |
| United States | NYSE, NASDAQ, NYSE ARCA |
| Europe | London, Frankfurt (XETRA), Paris, Amsterdam |
| Asia | Tokyo, Hong Kong, Singapore, Shanghai, Shenzhen |
| Others | Toronto, Sydney, São Paulo, and more |

## Stock Health Score

The Stock Health Score is a custom metric (0-100) that evaluates a stock's overall health based on four components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Return Score | 25% | Based on average daily returns |
| Volatility Score | 25% | Lower volatility = higher score |
| Trend Score | 25% | Short-term vs long-term MA ratio |
| Position Score | 25% | Current price vs 52-week high |

### Score Categories

- **Excellent (80-100)**: Strong performer with low risk
- **Good (60-79)**: Solid performance with acceptable risk
- **Fair (40-59)**: Average performance, monitor closely
- **Poor (20-39)**: Underperforming with elevated risk
- **Critical (0-19)**: Significant concerns across metrics

## Supported Stocks

The dashboard allows searching **any stock worldwide**, not just predefined ones. Popular stocks are shown by default:

| Symbol | Company Name | Sector |
|--------|--------------|--------|
| INFY.NS | Infosys Limited | IT |
| TCS.NS | Tata Consultancy Services | IT |
| RELIANCE.NS | Reliance Industries | Energy |
| AAPL | Apple Inc. | Technology |
| GOOGL | Alphabet Inc. | Technology |
| And many more... | | |

**Global Stock Support**: Simply search for any valid ticker symbol (e.g., `TSLA`, `AMZN`, `VOW3.DE`, `7203.T`).

## Technology Stack

- **Backend**: FastAPI (Python 3.9+)
- **Data Source**: Yahoo Finance (yfinance)
- **Data Processing**: Pandas, NumPy
- **Database**: SQLite (built-in caching)
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: Chart.js
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Architecture Decisions

1. **Modular Design**: Separate concerns into distinct modules (data fetching, utilities, database, models)
2. **Async Support**: FastAPI's async capabilities for better performance
3. **Caching Layer**: SQLite caching to minimize external API calls
4. **Type Safety**: Pydantic models for request/response validation
5. **Clean API**: RESTful design with proper HTTP methods and status codes

## Future Improvements

1. **Additional Indicators**: RSI, MACD, Bollinger Bands
2. **Portfolio Tracking**: User portfolios with P&L tracking
3. **Alerts System**: Price and indicator-based notifications
4. **Machine Learning**: Price prediction models
5. **WebSocket Support**: Real-time price updates
6. **Authentication**: User accounts and API keys
7. **Rate Limiting**: Protect against API abuse
8. **Docker Support**: Containerized deployment
9. **CI/CD Pipeline**: Automated testing and deployment

## Deployment

### Railway (Recommended - Free Tier)

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Deploy:
   ```bash
   cd stock-dashboard
   railway init
   railway up
   ```

3. Get your deployment URL:
   ```bash
   railway domain
   ```

### Docker (Local Development)

```bash
# Build image
docker build -t stock-dashboard .

# Run container
docker run -p 8007:8007 stock-dashboard
```

### Docker Compose

```bash
docker-compose up -d
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --host 0.0.0.0 --port 8007
```

## Error Handling

The API returns consistent error responses:

```json
{
  "error": "NotFound",
  "message": "Symbol 'INVALID.NS' is not in our supported list.",
  "symbol": "INVALID.NS"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper tests
4. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Contact

For questions or support, please open an issue on the repository.

---

Built with passion for the fintech community
