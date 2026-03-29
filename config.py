"""
Configuration Module

Central configuration for the Stock Data Intelligence Dashboard.
"""

# API Configuration
API_VERSION = "1.0.0"
API_TITLE = "Stock Data Intelligence Dashboard"

# Data Configuration
DEFAULT_DATA_PERIOD = "1y"  # 1 year of historical data
DEFAULT_DAYS_DISPLAY = 30   # Default days to show in API responses

# Cache Configuration
CACHE_DURATION_HOURS = 1    # How long to cache stock data

# Database Configuration
DATABASE_PATH = "stock_data.db"

# Market Configuration
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30
MARKET_TIMEZONE = "Asia/Kolkata"

# Health Score Weights
HEALTH_SCORE_WEIGHTS = {
    "return": 0.25,
    "volatility": 0.25,
    "trend": 0.25,
    "position": 0.25
}

# Technical Indicator Settings
MA_SHORT_WINDOW = 7
MA_LONG_WINDOW = 20
VOLATILITY_WINDOW = 20
TRADING_DAYS_PER_YEAR = 252


# ==========================================
# Standardized Sector Configuration
# ==========================================

# Master list of standardized sector names
STANDARD_SECTORS = [
    "Technology",
    "Financial Services",
    "Healthcare",
    "Consumer Cyclical",
    "Consumer Defensive",
    "Industrials",
    "Energy",
    "Utilities",
    "Real Estate",
    "Basic Materials",
    "Communication Services",
    "Automotive",
    "Aerospace & Defense",
    "Pharmaceuticals",
    "Biotechnology",
    "Telecommunications",
    "Media & Entertainment",
    "Retail",
    "E-Commerce",
    "Travel & Leisure",
    "Food & Beverage",
    "Agriculture",
    "Mining",
    "Oil & Gas",
    "Renewable Energy",
    "Construction",
    "Transportation",
    "Logistics",
    "Insurance",
    "Banking",
    "Asset Management",
    "Conglomerate",
    "Unknown"
]

# Mapping of various sector names to standardized names
# Key: lowercase variation, Value: standardized name
SECTOR_MAPPING = {
    # Technology variations
    "technology": "Technology",
    "information technology": "Technology",
    "information technology services": "Technology",
    "it": "Technology",
    "it services": "Technology",
    "software": "Technology",
    "software - infrastructure": "Technology",
    "software - application": "Technology",
    "software—infrastructure": "Technology",
    "software—application": "Technology",
    "internet content & information": "Technology",
    "internet software/services": "Technology",
    "computer hardware": "Technology",
    "semiconductors": "Technology",
    "semiconductor equipment & materials": "Technology",
    "electronic components": "Technology",
    "electronics": "Technology",
    "computer systems": "Technology",
    "data processing": "Technology",
    "tech": "Technology",
    "hardware": "Technology",
    "scientific & technical instruments": "Technology",
    "information technology hardware": "Technology",
    
    # Financial Services variations
    "financial services": "Financial Services",
    "financials": "Financial Services",
    "finance": "Financial Services",
    "financial": "Financial Services",
    "banking": "Banking",
    "banks": "Banking",
    "banks - regional": "Banking",
    "banks—regional": "Banking",
    "banks - diversified": "Banking",
    "banks—diversified": "Banking",
    "diversified banks": "Banking",
    "regional banks": "Banking",
    "private banks": "Banking",
    "public banks": "Banking",
    "insurance": "Insurance",
    "insurance - life": "Insurance",
    "insurance—life": "Insurance",
    "insurance - diversified": "Insurance",
    "insurance—diversified": "Insurance",
    "insurance - property & casualty": "Insurance",
    "insurance—property & casualty": "Insurance",
    "life insurance": "Insurance",
    "general insurance": "Insurance",
    "asset management": "Asset Management",
    "capital markets": "Asset Management",
    "investment banking": "Asset Management",
    "investment management": "Asset Management",
    "investment banking & brokerage": "Asset Management",
    "credit services": "Financial Services",
    "financial data & stock exchanges": "Financial Services",
    "financial conglomerates": "Financial Services",
    "mortgage finance": "Financial Services",
    "shell companies": "Financial Services",
    
    # Healthcare variations
    "healthcare": "Healthcare",
    "health care": "Healthcare",
    "healthcare plans": "Healthcare",
    "healthcare services": "Healthcare",
    "health care equipment & services": "Healthcare",
    "medical devices": "Healthcare",
    "medical instruments & supplies": "Healthcare",
    "medical care facilities": "Healthcare",
    "diagnostics & research": "Healthcare",
    "health information services": "Healthcare",
    "medical distribution": "Healthcare",
    "hospitals": "Healthcare",
    
    # Pharmaceuticals & Biotech
    "pharmaceuticals": "Pharmaceuticals",
    "drug manufacturers - general": "Pharmaceuticals",
    "drug manufacturers—general": "Pharmaceuticals",
    "drug manufacturers - specialty & generic": "Pharmaceuticals",
    "drug manufacturers—specialty & generic": "Pharmaceuticals",
    "pharmaceutical retailers": "Pharmaceuticals",
    "biotechnology": "Biotechnology",
    "biotech": "Biotechnology",
    
    # Consumer variations
    "consumer cyclical": "Consumer Cyclical",
    "consumer discretionary": "Consumer Cyclical",
    "consumer durables": "Consumer Cyclical",
    "consumer goods": "Consumer Defensive",
    "consumer defensive": "Consumer Defensive",
    "consumer staples": "Consumer Defensive",
    "consumer non-durables": "Consumer Defensive",
    "consumer products": "Consumer Defensive",
    "household & personal products": "Consumer Defensive",
    "household products": "Consumer Defensive",
    "personal products": "Consumer Defensive",
    "packaged foods": "Food & Beverage",
    "beverages - non-alcoholic": "Food & Beverage",
    "beverages—non-alcoholic": "Food & Beverage",
    "beverages - alcoholic": "Food & Beverage",
    "beverages—wineries & distilleries": "Food & Beverage",
    "food products": "Food & Beverage",
    "food & beverage": "Food & Beverage",
    "tobacco": "Consumer Defensive",
    "fmcg": "Consumer Defensive",
    "fast moving consumer goods": "Consumer Defensive",
    
    # Retail & E-Commerce
    "retail": "Retail",
    "retail - cyclical": "Retail",
    "retail—cyclical": "Retail",
    "retail - defensive": "Retail",
    "retail—defensive": "Retail",
    "specialty retail": "Retail",
    "department stores": "Retail",
    "discount stores": "Retail",
    "grocery stores": "Retail",
    "home improvement retail": "Retail",
    "apparel retail": "Retail",
    "internet retail": "E-Commerce",
    "e-commerce": "E-Commerce",
    "online retail": "E-Commerce",
    
    # Energy variations
    "energy": "Energy",
    "oil & gas": "Oil & Gas",
    "oil & gas integrated": "Oil & Gas",
    "oil & gas e&p": "Oil & Gas",
    "oil & gas exploration & production": "Oil & Gas",
    "oil & gas refining & marketing": "Oil & Gas",
    "oil & gas midstream": "Oil & Gas",
    "oil & gas equipment & services": "Oil & Gas",
    "oil & gas drilling": "Oil & Gas",
    "petroleum": "Oil & Gas",
    "crude oil": "Oil & Gas",
    "natural gas": "Oil & Gas",
    "renewable energy": "Renewable Energy",
    "solar": "Renewable Energy",
    "wind energy": "Renewable Energy",
    "clean energy": "Renewable Energy",
    "utilities - renewable": "Renewable Energy",
    "utilities—renewable": "Renewable Energy",
    
    # Utilities variations
    "utilities": "Utilities",
    "utilities - regulated electric": "Utilities",
    "utilities—regulated electric": "Utilities",
    "utilities - regulated gas": "Utilities",
    "utilities—regulated gas": "Utilities",
    "utilities - diversified": "Utilities",
    "utilities—diversified": "Utilities",
    "utilities - independent power producers": "Utilities",
    "utilities—independent power producers": "Utilities",
    "electric utilities": "Utilities",
    "gas utilities": "Utilities",
    "water utilities": "Utilities",
    "power generation": "Utilities",
    "power": "Utilities",
    
    # Industrials variations
    "industrials": "Industrials",
    "industrial": "Industrials",
    "industrial goods": "Industrials",
    "industrial conglomerates": "Conglomerate",
    "diversified industrials": "Industrials",
    "machinery": "Industrials",
    "specialty industrial machinery": "Industrials",
    "farm & heavy construction machinery": "Industrials",
    "industrial machinery": "Industrials",
    "electrical equipment & parts": "Industrials",
    "electrical equipment": "Industrials",
    "building products & equipment": "Industrials",
    "metal fabrication": "Industrials",
    "tools & accessories": "Industrials",
    "pollution & treatment controls": "Industrials",
    "waste management": "Industrials",
    "engineering & construction": "Construction",
    "infrastructure": "Construction",
    "construction": "Construction",
    "building materials": "Construction",
    "cement": "Construction",
    "residential construction": "Construction",
    "construction materials": "Construction",
    
    # Transportation & Logistics
    "transportation": "Transportation",
    "airlines": "Transportation",
    "airports & air services": "Transportation",
    "railroads": "Transportation",
    "trucking": "Transportation",
    "marine shipping": "Transportation",
    "shipping": "Transportation",
    "logistics": "Logistics",
    "integrated freight & logistics": "Logistics",
    "air freight & logistics": "Logistics",
    
    # Automotive variations
    "automotive": "Automotive",
    "auto manufacturers": "Automotive",
    "auto - manufacturers": "Automotive",
    "auto—manufacturers": "Automotive",
    "auto parts": "Automotive",
    "auto - parts": "Automotive",
    "auto—parts": "Automotive",
    "automobiles": "Automotive",
    "automobile manufacturers": "Automotive",
    "auto components": "Automotive",
    "auto dealerships": "Automotive",
    "vehicles": "Automotive",
    "two wheelers": "Automotive",
    "commercial vehicles": "Automotive",
    
    # Communication & Media
    "communication services": "Communication Services",
    "communication": "Communication Services",
    "communications": "Communication Services",
    "telecommunication": "Telecommunications",
    "telecommunications": "Telecommunications",
    "telecom": "Telecommunications",
    "telecom services": "Telecommunications",
    "telecom - wireless": "Telecommunications",
    "telecom—wireless": "Telecommunications",
    "wireless telecommunications": "Telecommunications",
    "media": "Media & Entertainment",
    "media - diversified": "Media & Entertainment",
    "media—diversified": "Media & Entertainment",
    "entertainment": "Media & Entertainment",
    "broadcasting": "Media & Entertainment",
    "publishing": "Media & Entertainment",
    "advertising agencies": "Media & Entertainment",
    "electronic gaming & multimedia": "Media & Entertainment",
    "gaming": "Media & Entertainment",
    
    # Real Estate
    "real estate": "Real Estate",
    "real estate - development": "Real Estate",
    "real estate—development": "Real Estate",
    "real estate - diversified": "Real Estate",
    "real estate—diversified": "Real Estate",
    "real estate services": "Real Estate",
    "reit": "Real Estate",
    "reit - diversified": "Real Estate",
    "reit—diversified": "Real Estate",
    "reit - retail": "Real Estate",
    "reit—retail": "Real Estate",
    "reit - residential": "Real Estate",
    "reit—residential": "Real Estate",
    "reit - office": "Real Estate",
    "reit—office": "Real Estate",
    "reit - industrial": "Real Estate",
    "reit—industrial": "Real Estate",
    "property": "Real Estate",
    "property development": "Real Estate",
    
    # Basic Materials
    "basic materials": "Basic Materials",
    "materials": "Basic Materials",
    "chemicals": "Basic Materials",
    "specialty chemicals": "Basic Materials",
    "agricultural inputs": "Basic Materials",
    "steel": "Basic Materials",
    "metals & mining": "Mining",
    "mining": "Mining",
    "gold": "Mining",
    "silver": "Mining",
    "copper": "Mining",
    "aluminum": "Basic Materials",
    "paper & paper products": "Basic Materials",
    "lumber & wood production": "Basic Materials",
    "coking coal": "Mining",
    "other industrial metals & mining": "Mining",
    "other precious metals & mining": "Mining",
    
    # Aerospace & Defense
    "aerospace & defense": "Aerospace & Defense",
    "aerospace": "Aerospace & Defense",
    "defense": "Aerospace & Defense",
    "defence": "Aerospace & Defense",
    "security & protection services": "Aerospace & Defense",
    
    # Travel & Leisure
    "travel & leisure": "Travel & Leisure",
    "travel services": "Travel & Leisure",
    "lodging": "Travel & Leisure",
    "resorts & casinos": "Travel & Leisure",
    "restaurants": "Travel & Leisure",
    "leisure": "Travel & Leisure",
    "hotels": "Travel & Leisure",
    "gambling": "Travel & Leisure",
    
    # Agriculture
    "agriculture": "Agriculture",
    "farm products": "Agriculture",
    "agricultural products": "Agriculture",
    "agribusiness": "Agriculture",
    "agricultural commodities": "Agriculture",
    
    # Conglomerate
    "conglomerate": "Conglomerate",
    "conglomerates": "Conglomerate",
    "diversified": "Conglomerate",
    "diversified operations": "Conglomerate",
    "multi-sector holdings": "Conglomerate",
    
    # Unknown/Other
    "n/a": "Unknown",
    "na": "Unknown",
    "none": "Unknown",
    "other": "Unknown",
    "miscellaneous": "Unknown",
    "": "Unknown",
}

# Sector colors for UI display (hex colors)
SECTOR_COLORS = {
    "Technology": "#00d4ff",
    "Financial Services": "#4CAF50",
    "Banking": "#2E7D32",
    "Insurance": "#66BB6A",
    "Asset Management": "#81C784",
    "Healthcare": "#E91E63",
    "Pharmaceuticals": "#AD1457",
    "Biotechnology": "#F06292",
    "Consumer Cyclical": "#FF9800",
    "Consumer Defensive": "#FFC107",
    "Food & Beverage": "#FFB300",
    "Retail": "#FF7043",
    "E-Commerce": "#FF5722",
    "Industrials": "#795548",
    "Energy": "#F44336",
    "Oil & Gas": "#D32F2F",
    "Renewable Energy": "#43A047",
    "Utilities": "#9C27B0",
    "Real Estate": "#00BCD4",
    "Basic Materials": "🧱",
    "Mining": "#455A64",
    "Communication Services": "#3F51B5",
    "Telecommunications": "#303F9F",
    "Media & Entertainment": "#7C4DFF",
    "Automotive": "#EF5350",
    "Aerospace & Defense": "#5C6BC0",
    "Travel & Leisure": "#26A69A",
    "Agriculture": "#8BC34A",
    "Transportation": "#78909C",
    "Logistics": "#546E7A",
    "Construction": "#8D6E63",
    "Conglomerate": "#9E9E9E",
    "Unknown": "#616161",
}

# Sector icons (emoji/unicode) for UI
SECTOR_ICONS = {
    "Technology": "💻",
    "Financial Services": "💰",
    "Banking": "🏦",
    "Insurance": "🛡️",
    "Asset Management": "📊",
    "Healthcare": "🏥",
    "Pharmaceuticals": "💊",
    "Biotechnology": "🧬",
    "Consumer Cyclical": "🛍️",
    "Consumer Defensive": "🏠",
    "Food & Beverage": "🍔",
    "Retail": "🏪",
    "E-Commerce": "🛒",
    "Industrials": "🏭",
    "Energy": "⚡",
    "Oil & Gas": "🛢️",
    "Renewable Energy": "☀️",
    "Utilities": "💡",
    "Real Estate": "🏢",
    "Basic Materials": "🧱",
    "Mining": "⛏️",
    "Communication Services": "📡",
    "Telecommunications": "📱",
    "Media & Entertainment": "🎬",
    "Automotive": "🚗",
    "Aerospace & Defense": "✈️",
    "Travel & Leisure": "🏖️",
    "Agriculture": "🌾",
    "Transportation": "🚚",
    "Logistics": "📦",
    "Construction": "🏗️",
    "Conglomerate": "🏛️",
    "Unknown": "❓",
}
