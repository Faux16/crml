#Holds default currency data and derived mappings for CRML FX logic.
DEFAULT_CURRENCIES = {
    "USD": {"symbol": "$",   "rate": 1.0},       # US Dollar (base currency)
    "EUR": {"symbol": "€",   "rate": 1.16},      # Euro
    "GBP": {"symbol": "£",   "rate": 1.02},      # British Pound
    "CHF": {"symbol": "Fr",  "rate": 1.09},      # Swiss Franc
    "JPY": {"symbol": "¥",   "rate": 0.0064},    # Japanese Yen
    "CNY": {"symbol": "CN¥", "rate": 0.142},     # Chinese Yuan
    "CAD": {"symbol": "C$",  "rate": 0.72},      # Canadian Dollar
    "AUD": {"symbol": "A$",  "rate": 0.66},      # Australian Dollar
    "INR": {"symbol": "₹",   "rate": 0.0111},    # Indian Rupee
    "BRL": {"symbol": "R$",  "rate": 0.18},      # Brazilian Real
    "PKR": {"symbol": "₨",   "rate": 0.0036},    # Pakistani Rupee
    "MXN": {"symbol": "MX$", "rate": 0.055},     # Mexican Peso
    "KRW": {"symbol": "₩",   "rate": 0.00068},   # South Korean Won
    "SGD": {"symbol": "S$",  "rate": 0.77},      # Singapore Dollar
    "HKD": {"symbol": "HK$", "rate": 0.129},     # Hong Kong Dollar
}

DEFAULT_FX_RATES = {code: info["rate"] for code, info in DEFAULT_CURRENCIES.items()}
CURRENCY_SYMBOL_TO_CODE = {info["symbol"]: code for code, info in DEFAULT_CURRENCIES.items()}
CURRENCY_CODE_TO_SYMBOL = {code: info["symbol"] for code, info in DEFAULT_CURRENCIES.items()}
