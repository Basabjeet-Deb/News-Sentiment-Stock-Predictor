// Stock name to ticker mapping
const STOCK_LOOKUP = {
    // Tech Giants
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'amazon': 'AMZN',
    'facebook': 'META',
    'meta': 'META',
    'tesla': 'TSLA',
    'nvidia': 'NVDA',
    'netflix': 'NFLX',
    'intel': 'INTC',
    'amd': 'AMD',
    'advanced micro devices': 'AMD',
    'salesforce': 'CRM',
    'oracle': 'ORCL',
    'adobe': 'ADBE',
    'cisco': 'CSCO',
    'broadcom': 'AVGO',
    'qualcomm': 'QCOM',
    'texas instruments': 'TXN',
    'intuit': 'INTU',
    'servicenow': 'NOW',
    
    // Finance
    'jpmorgan': 'JPM',
    'jp morgan': 'JPM',
    'bank of america': 'BAC',
    'wells fargo': 'WFC',
    'goldman sachs': 'GS',
    'morgan stanley': 'MS',
    'citigroup': 'C',
    'citi': 'C',
    'visa': 'V',
    'mastercard': 'MA',
    'paypal': 'PYPL',
    'square': 'SQ',
    'coinbase': 'COIN',
    'american express': 'AXP',
    'amex': 'AXP',
    'charles schwab': 'SCHW',
    'schwab': 'SCHW',
    'blackrock': 'BLK',
    
    // Retail
    'walmart': 'WMT',
    'target': 'TGT',
    'costco': 'COST',
    'home depot': 'HD',
    'lowes': 'LOW',
    'nike': 'NKE',
    'starbucks': 'SBUX',
    'mcdonalds': 'MCD',
    'mcdonald': 'MCD',
    'chipotle': 'CMG',
    'dollar general': 'DG',
    'tjx': 'TJX',
    'ross': 'ROST',
    'best buy': 'BBY',
    'gap': 'GPS',
    'lululemon': 'LULU',
    'lulu': 'LULU',
    
    // E-commerce
    'shopify': 'SHOP',
    'ebay': 'EBAY',
    'etsy': 'ETSY',
    'wayfair': 'W',
    'chewy': 'CHWY',
    'carvana': 'CVNA',
    
    // Healthcare
    'johnson & johnson': 'JNJ',
    'johnson and johnson': 'JNJ',
    'jnj': 'JNJ',
    'unitedhealth': 'UNH',
    'united health': 'UNH',
    'pfizer': 'PFE',
    'abbvie': 'ABBV',
    'merck': 'MRK',
    'thermo fisher': 'TMO',
    'abbott': 'ABT',
    'eli lilly': 'LLY',
    'lilly': 'LLY',
    'bristol myers': 'BMY',
    'amgen': 'AMGN',
    'gilead': 'GILD',
    'cvs': 'CVS',
    'moderna': 'MRNA',
    
    // Automotive
    'ford': 'F',
    'general motors': 'GM',
    'gm': 'GM',
    'rivian': 'RIVN',
    'lucid': 'LCID',
    'nio': 'NIO',
    
    // Energy
    'exxon': 'XOM',
    'exxon mobil': 'XOM',
    'chevron': 'CVX',
    'conocophillips': 'COP',
    'schlumberger': 'SLB',
    'halliburton': 'HAL',
    'marathon': 'MPC',
    'valero': 'VLO',
    'occidental': 'OXY',
    
    // Aerospace/Defense
    'lockheed': 'LMT',
    'lockheed martin': 'LMT',
    'boeing': 'BA',
    'raytheon': 'RTX',
    'northrop': 'NOC',
    'northrop grumman': 'NOC',
    'general dynamics': 'GD',
    
    // Entertainment
    'disney': 'DIS',
    'walt disney': 'DIS',
    'comcast': 'CMCSA',
    'warner bros': 'WBD',
    'paramount': 'PARA',
    'spotify': 'SPOT',
    'roblox': 'RBLX',
    
    // Semiconductors
    'tsmc': 'TSM',
    'taiwan semiconductor': 'TSM',
    'asml': 'ASML',
    'micron': 'MU',
    'micron technology': 'MU',
    'applied materials': 'AMAT',
    'lam research': 'LRCX',
    'kla': 'KLAC',
    'kla corporation': 'KLAC',
    'marvell': 'MRVL',
    'marvell technology': 'MRVL',
    'on semiconductor': 'ON',
    'monolithic power': 'MPWR',
    'skyworks': 'SWKS',
    'qorvo': 'QRVO',
    
    // Cloud/Software
    'snowflake': 'SNOW',
    'datadog': 'DDOG',
    'cloudflare': 'NET',
    'mongodb': 'MDB',
    'atlassian': 'TEAM',
    'zscaler': 'ZS',
    'crowdstrike': 'CRWD',
    'palo alto': 'PANW',
    'palo alto networks': 'PANW',
    'workday': 'WDAY',
    'autodesk': 'ADSK',
    
    // Telecom
    'att': 'T',
    'at&t': 'T',
    'verizon': 'VZ',
    't-mobile': 'TMUS',
    'tmobile': 'TMUS',
    
    // Consumer Goods
    'procter gamble': 'PG',
    'procter & gamble': 'PG',
    'pg': 'PG',
    'coca cola': 'KO',
    'coca-cola': 'KO',
    'coke': 'KO',
    'pepsi': 'PEP',
    'pepsico': 'PEP',
    'philip morris': 'PM',
    'colgate': 'CL',
    'kimberly clark': 'KMB',
    'general mills': 'GIS',
    'kellogg': 'K',
    'hershey': 'HSY',
    
    // Industrials
    'caterpillar': 'CAT',
    'deere': 'DE',
    'john deere': 'DE',
    'general electric': 'GE',
    'ge': 'GE',
    'honeywell': 'HON',
    'ups': 'UPS',
    'united parcel': 'UPS',
    'fedex': 'FDX',
    'union pacific': 'UNP',
    '3m': 'MMM',
    'emerson': 'EMR',
    'emerson electric': 'EMR',
    'illinois tool': 'ITW',
    'eaton': 'ETN',
    
    // Real Estate
    'american tower': 'AMT',
    'prologis': 'PLD',
    'crown castle': 'CCI',
    'equinix': 'EQIX',
    'public storage': 'PSA',
    'simon property': 'SPG',
    'realty income': 'O',
    'welltower': 'WELL',
    'digital realty': 'DLR',
    'avalonbay': 'AVB',
    
    // Utilities
    'nextera': 'NEE',
    'duke energy': 'DUK',
    'southern company': 'SO',
    'dominion': 'D',
    
    // Crypto
    'microstrategy': 'MSTR',
    'marathon digital': 'MARA',
    'riot platforms': 'RIOT',
    'riot blockchain': 'RIOT',
    
    // Food & Beverage
    'yum brands': 'YUM',
    'yum': 'YUM',
    'dominos': 'DPZ',
    'domino': 'DPZ',
    'starbucks': 'SBUX',
    'dunkin': 'DNKN',
    'wendys': 'WEN',
    'burger king': 'QSR',
    
    // Airlines
    'delta': 'DAL',
    'american airlines': 'AAL',
    'united airlines': 'UAL',
    'southwest': 'LUV',
    
    // Hotels
    'marriott': 'MAR',
    'hilton': 'HLT',
    'airbnb': 'ABNB',
    'booking': 'BKNG',
    'booking.com': 'BKNG',
    
    // Ride Sharing
    'uber': 'UBER',
    'lyft': 'LYFT',
    'doordash': 'DASH',
    
    // Social Media
    'twitter': 'TWTR',
    'x': 'TWTR',
    'snap': 'SNAP',
    'snapchat': 'SNAP',
    'pinterest': 'PINS',
    'reddit': 'RDDT',
};

// Function to find ticker from search term
function findTicker(searchTerm) {
    const term = searchTerm.toLowerCase().trim();
    
    // First check if it's already a ticker (uppercase, 1-5 chars)
    if (term.length <= 5 && term === term.toUpperCase()) {
        return term.toUpperCase();
    }
    
    // Check exact match in lookup
    if (STOCK_LOOKUP[term]) {
        return STOCK_LOOKUP[term];
    }
    
    // Check partial matches
    for (const [name, ticker] of Object.entries(STOCK_LOOKUP)) {
        if (name.includes(term) || term.includes(name)) {
            return ticker;
        }
    }
    
    // If nothing found, assume it's a ticker and uppercase it
    return term.toUpperCase();
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { STOCK_LOOKUP, findTicker };
}
