// Main Application Logic
let allPredictions = [];
let allStocks = [];
let allNews = [];

// DOM Elements
const pages = {
    dashboard: document.getElementById('dashboard-page'),
    predictions: document.getElementById('predictions-page'),
    stocks: document.getElementById('stocks-page'),
    news: document.getElementById('news-page')
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // Wait for chart library to load
    if (typeof LightweightCharts === 'undefined') {
        console.warn('Chart library not loaded yet, waiting...');
        setTimeout(() => {
            if (typeof LightweightCharts === 'undefined') {
                console.error('Chart library failed to load!');
            }
        }, 2000);
    }
    
    setupNavigation();
    setupFilters();
    setupPipeline();
    loadDashboard();
});

// Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            
            // Update active nav
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            // Show page
            Object.values(pages).forEach(p => p.classList.remove('active'));
            pages[page].classList.add('active');
            
            // Update title
            document.getElementById('page-title').textContent = 
                page.charAt(0).toUpperCase() + page.slice(1);
            
            // Load page data
            loadPage(page);
        });
    });
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        const activePage = document.querySelector('.nav-item.active').dataset.page;
        loadPage(activePage);
    });
}

// Load page data
function loadPage(page) {
    switch(page) {
        case 'dashboard': loadDashboard(); break;
        case 'predictions': loadPredictions(); break;
        case 'stocks': loadStocks(); break;
        case 'news': loadNews(); break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        // Load all data in parallel
        const [summary, topPicks, bottomPicks, gainers, losers, news] = await Promise.all([
            API.getPredictionSummary(),
            API.getTopPredictions(5),
            API.getBottomPredictions(5),
            API.getTopGainers(5),
            API.getTopLosers(5),
            API.getNews()
        ]);
        
        // Update summary cards
        document.getElementById('strong-buy-count').textContent = 
            (summary.strong_buy_count || 0) + (summary.buy_count || 0);
        document.getElementById('hold-count').textContent = 
            summary.hold_count || 0;
        document.getElementById('strong-sell-count').textContent = 
            (summary.strong_sell_count || 0) + (summary.sell_count || 0);
        document.getElementById('total-stocks').textContent = summary.total_stocks || 0;
        
        // Top picks
        renderList('top-picks', topPicks.top_picks || [], (p) => ({
            ticker: p.ticker,
            details: p.recommendation,
            value: `${((p.prediction_score || p.final_score || 0) * 100).toFixed(0)}%`,
            valueClass: 'positive'
        }));
        
        // Top sells
        renderList('top-sells', bottomPicks.sell_candidates || [], (p) => ({
            ticker: p.ticker,
            details: p.recommendation,
            value: `${((p.prediction_score || p.final_score || 0) * 100).toFixed(0)}%`,
            valueClass: 'negative'
        }));
        
        // Gainers
        renderList('top-gainers', gainers.gainers || [], (s) => ({
            ticker: s.ticker,
            details: `$${parseFloat(s.price || s.current_price || 0).toFixed(2)}`,
            value: `+${parseFloat(s.change_percent || 0).toFixed(2)}%`,
            valueClass: 'positive'
        }));
        
        // Losers
        renderList('top-losers', losers.losers || [], (s) => ({
            ticker: s.ticker,
            details: `$${parseFloat(s.price || s.current_price || 0).toFixed(2)}`,
            value: `${parseFloat(s.change_percent || 0).toFixed(2)}%`,
            valueClass: 'negative'
        }));
        
        // Recent news
        renderNewsGrid('recent-news', (news.articles || []).slice(0, 6));
        
        // Update timestamp
        document.getElementById('last-updated').textContent = 
            `Last updated: ${new Date().toLocaleTimeString()}`;
            
    } catch (err) {
        console.error('Failed to load dashboard:', err);
        showError('Failed to connect to API. Is the server running?');
    }
}

// Predictions Page
async function loadPredictions() {
    try {
        const data = await API.getPredictions();
        allPredictions = data.predictions || [];
        renderPredictionsTable(allPredictions);
    } catch (err) {
        console.error('Failed to load predictions:', err);
    }
}

function renderPredictionsTable(predictions) {
    const tbody = document.getElementById('predictions-tbody');
    
    if (!predictions.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No predictions found</td></tr>';
        return;
    }
    
    tbody.innerHTML = predictions.map(p => `
        <tr class="clickable-row" onclick="openStockModal('${p.ticker}')">
            <td><strong>${p.ticker}</strong></td>
            <td><span class="badge ${getBadgeClass(p.recommendation)}">${p.recommendation}</span></td>
            <td class="${(p.avg_sentiment || p.sentiment_score || 0) >= 0 ? 'positive' : 'negative'}">
                ${((p.avg_sentiment || p.sentiment_score || 0) * 100).toFixed(0)}%
            </td>
            <td class="${(p.price_change_percent || p.price_change || 0) >= 0 ? 'positive' : 'negative'}">
                ${(p.price_change_percent || p.price_change || 0) >= 0 ? '+' : ''}${parseFloat(p.price_change_percent || (p.price_change * 100) || 0).toFixed(2)}%
            </td>
            <td><strong>${((p.prediction_score || p.final_score || 0) * 100).toFixed(0)}%</strong></td>
        </tr>
    `).join('');
}

// Stocks Page
async function loadStocks() {
    try {
        const data = await API.getStocks();
        allStocks = data.prices || data.stocks || [];
        renderStocksTable(allStocks);
    } catch (err) {
        console.error('Failed to load stocks:', err);
    }
}

function renderStocksTable(stocks) {
    const tbody = document.getElementById('stocks-tbody');
    
    if (!stocks.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No stock data found</td></tr>';
        return;
    }
    
    tbody.innerHTML = stocks.map(s => {
        const price = parseFloat(s.price || s.current_price) || 0;
        const change = parseFloat(s.change) || 0;
        const changePct = parseFloat(s.change_percent) || 0;
        const volume = parseInt(s.volume) || 0;
        
        return `
            <tr>
