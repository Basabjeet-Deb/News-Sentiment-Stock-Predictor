// API Service - Handles all backend communication
const API_BASE = 'http://localhost:8000/api/v1';

const API = {
    // Predictions
    async getPredictions() {
        const res = await fetch(`${API_BASE}/predictions/`);
        return res.json();
    },
    
    async getTopPredictions(count = 10) {
        const res = await fetch(`${API_BASE}/predictions/top?count=${count}`);
        return res.json();
    },
    
    async getBottomPredictions(count = 10) {
        const res = await fetch(`${API_BASE}/predictions/bottom?count=${count}`);
        return res.json();
    },
    
    async getPredictionSummary() {
        const res = await fetch(`${API_BASE}/predictions/summary`);
        return res.json();
    },
    
    async getPredictionByTicker(ticker) {
        const res = await fetch(`${API_BASE}/predictions/${ticker}`);
        return res.json();
    },
    
    // Stocks
    async getStocks() {
        const res = await fetch(`${API_BASE}/stocks/`);
        return res.json();
    },
    
    async getStock(ticker) {
        const res = await fetch(`${API_BASE}/stocks/${ticker}`);
        return res.json();
    },
    
    async getStockHistory(ticker, period = '1y', interval = '1d') {
        const res = await fetch(`${API_BASE}/stocks/${ticker}/history?period=${period}&interval=${interval}`);
        return res.json();
    },
    
    async getTopGainers(count = 10) {
        const res = await fetch(`${API_BASE}/stocks/gainers?count=${count}`);
        return res.json();
    },
    
    async getTopLosers(count = 10) {
        const res = await fetch(`${API_BASE}/stocks/losers?count=${count}`);
        return res.json();
    },
    
    async getStockSummary() {
        const res = await fetch(`${API_BASE}/stocks/summary`);
        return res.json();
    },
    
    // News
    async getNews() {
        const res = await fetch(`${API_BASE}/news/`);
        return res.json();
    },
    
    async getNewsByTicker(ticker) {
        const res = await fetch(`${API_BASE}/news/by-ticker/${ticker}`);
        return res.json();
    },
    
    async getNewsSummary() {
        const res = await fetch(`${API_BASE}/news/summary`);
        return res.json();
    },
    
    // Pipeline
    async getPipelineStatus() {
        const res = await fetch(`${API_BASE}/pipeline/status`);
        return res.json();
    },
    
    async runPipeline() {
        const res = await fetch(`${API_BASE}/pipeline/run`, { method: 'POST' });
        return res.json();
    },
    
    // Training API Stubs
    async collectHistoricalData(months, tickers) {
        try {
            const res = await fetch(`${API_BASE}/training/collect-data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ months, tickers })
            });
            return res.json();
        } catch (e) {
            return { status: "simulated" };
        }
    },
    
    async trainModel() {
        try {
            const res = await fetch(`${API_BASE}/training/train-model`, {
                method: 'POST'
            });
            return res.json();
        } catch (e) {
            return { status: "simulated" };
        }
    },
    
    // Health
    async healthCheck() {
        const res = await fetch('/health');
        return res.json();
    }
};
