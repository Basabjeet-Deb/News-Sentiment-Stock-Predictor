// Ticker to company name mapping
const TICKER_NAMES = {
    // Tech
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google',
    'AMZN': 'Amazon',
    'META': 'Meta (Facebook)',
    'TSLA': 'Tesla',
    'NVDA': 'NVIDIA',
    'NFLX': 'Netflix',
    'INTC': 'Intel',
    'AMD': 'AMD',
    'CRM': 'Salesforce',
    'ORCL': 'Oracle',
    'ADBE': 'Adobe',
    'CSCO': 'Cisco',
    'AVGO': 'Broadcom',
    'QCOM': 'Qualcomm',
    'TXN': 'Texas Instruments',
    'INTU': 'Intuit',
    'NOW': 'ServiceNow',
    
    // Finance
    'JPM': 'JPMorgan Chase',
    'BAC': 'Bank of America',
    'WFC': 'Wells Fargo',
    'GS': 'Goldman Sachs',
    'MS': 'Morgan Stanley',
    'C': 'Citigroup',
    'V': 'Visa',
    'MA': 'Mastercard',
    'PYPL': 'PayPal',
    'SQ': 'Block (Square)',
    'COIN': 'Coinbase',
    'AXP': 'American Express',
    'SCHW': 'Charles Schwab',
    'BLK': 'BlackRock',
    
    // Retail
    'WMT': 'Walmart',
    'TGT': 'Target',
    'COST': 'Costco',
    'HD': 'Home Depot',
    'LOW': "Lowe's",
    'NKE': 'Nike',
    'SBUX': 'Starbucks',
    'MCD': "McDonald's",
    'CMG': 'Chipotle',
    'YUM': 'Yum! Brands',
    'DG': 'Dollar General',
    'TJX': 'TJX Companies',
    'ROST': 'Ross Stores',
    'BBY': 'Best Buy',
    'LULU': 'Lululemon',
    
    // Healthcare
    'JNJ': 'Johnson & Johnson',
    'UNH': 'UnitedHealth',
    'PFE': 'Pfizer',
    'ABBV': 'AbbVie',
    'MRK': 'Merck',
    'TMO': 'Thermo Fisher',
    'ABT': 'Abbott Labs',
    'LLY': 'Eli Lilly',
    'BMY': 'Bristol Myers',
    'AMGN': 'Amgen',
    'GILD': 'Gilead Sciences',
    'CVS': 'CVS Health',
    'MRNA': 'Moderna',
    
    // Energy
    'XOM': 'Exxon Mobil',
    'CVX': 'Chevron',
    'COP': 'ConocoPhillips',
    'SLB': 'Schlumberger',
    'HAL': 'Halliburton',
    'MPC': 'Marathon Petroleum',
    'PSX': 'Phillips 66',
    'VLO': 'Valero Energy',
    'OXY': 'Occidental Petroleum',
    'BKR': 'Baker Hughes',
    
    // Automotive
    'F': 'Ford',
    'GM': 'General Motors',
    'RIVN': 'Rivian',
    'LCID': 'Lucid Motors',
    'NIO': 'NIO Inc.',
    
    // Aerospace/Defense
    'LMT': 'Lockheed Martin',
    'BA': 'Boeing',
    'RTX': 'Raytheon',
    'NOC': 'Northrop Grumman',
    'GD': 'General Dynamics',
    
    // Entertainment
    'DIS': 'Disney',
    'CMCSA': 'Comcast',
    'NFLX': 'Netflix',
    'PARA': 'Paramount',
    'WBD': 'Warner Bros Discovery',
    'SPOT': 'Spotify',
    'RBLX': 'Roblox',
    
    // Semiconductors
    'TSM': 'TSMC',
    'ASML': 'ASML',
    'MU': 'Micron',
    'AMAT': 'Applied Materials',
    'LRCX': 'Lam Research',
    'KLAC': 'KLA Corporation',
    'MRVL': 'Marvell',
    
    // Cloud/Software
    'SNOW': 'Snowflake',
    'DDOG': 'Datadog',
    'NET': 'Cloudflare',
    'MDB': 'MongoDB',
    'TEAM': 'Atlassian',
    'ZS': 'Zscaler',
    'CRWD': 'CrowdStrike',
    'PANW': 'Palo Alto Networks',
    'WDAY': 'Workday',
    
    // E-commerce
    'SHOP': 'Shopify',
    'EBAY': 'eBay',
    'ETSY': 'Etsy',
    'W': 'Wayfair',
    
    // Telecom
    'T': 'AT&T',
    'VZ': 'Verizon',
    'TMUS': 'T-Mobile',
    
    // Consumer Goods
    'PG': 'Procter & Gamble',
    'KO': 'Coca-Cola',
    'PEP': 'PepsiCo',
    'PM': 'Philip Morris',
    'CL': 'Colgate-Palmolive',
    'KMB': 'Kimberly-Clark',
    'GIS': 'General Mills',
    'K': "Kellogg's",
    'HSY': 'Hershey',
    
    // Industrials
    'CAT': 'Caterpillar',
    'DE': 'John Deere',
    'GE': 'General Electric',
    'HON': 'Honeywell',
    'UPS': 'UPS',
    'FDX': 'FedEx',
    'UNP': 'Union Pacific',
    'MMM': '3M',
    
    // Real Estate
    'AMT': 'American Tower',
    'PLD': 'Prologis',
    'CCI': 'Crown Castle',
    'EQIX': 'Equinix',
    'PSA': 'Public Storage',
    'SPG': 'Simon Property',
    'O': 'Realty Income',
    'WELL': 'Welltower',
    
    // Crypto
    'MSTR': 'MicroStrategy',
    'MARA': 'Marathon Digital',
    'RIOT': 'Riot Platforms',
};

// Function to get company name from ticker
function getCompanyName(ticker) {
    return TICKER_NAMES[ticker.toUpperCase()] || ticker;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TICKER_NAMES, getCompanyName };
}
