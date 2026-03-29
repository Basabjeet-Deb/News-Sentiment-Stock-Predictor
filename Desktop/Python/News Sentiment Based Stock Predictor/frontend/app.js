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
                <td><strong>${s.ticker}</strong></td>
                <td>$${price.toFixed(2)}</td>
                <td class="${change >= 0 ? 'positive' : 'negative'}">
                    ${change >= 0 ? '+' : ''}$${change.toFixed(2)}
                </td>
                <td class="${changePct >= 0 ? 'positive' : 'negative'}">
                    ${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%
                </td>
                <td>${formatVolume(volume)}</td>
            </tr>
        `;
    }).join('');
}

// News Page
async function loadNews() {
    try {
        const data = await API.getNews();
        allNews = data.articles || [];
        renderNewsList(allNews);
    } catch (err) {
        console.error('Failed to load news:', err);
    }
}

function renderNewsList(articles) {
    const container = document.getElementById('news-list');
    
    if (!articles.length) {
        container.innerHTML = '<p class="loading">No news articles found</p>';
        return;
    }
    
    container.innerHTML = articles.map(a => {
        // Get sentiment score from multiple possible fields
        const sentimentScore = parseFloat(
            a.sentiment_compound || 
            a.sentiment_score || 
            (a.sentiment && typeof a.sentiment === 'object' && a.sentiment.compound) || 
            0
        );
        
        const sentimentDisplay = getSentimentDisplay(sentimentScore);
        
        return `
            <div class="news-list-item">
                <div class="headline">${a.title || 'No title'}</div>
                <div class="summary">${a.summary || a.description || ''}</div>
                <div class="meta">
                    <span class="sentiment ${sentimentDisplay.color}">
                        ${sentimentDisplay.emoji} ${sentimentDisplay.label}
                    </span>
                    <span>${a.ticker || 'General'}</span>
                    <span>${formatDate(a.published_date || a.published_at || a.date)}</span>
                    ${a.source ? `<span>${a.source}</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Filters
function setupFilters() {
    // Prediction filters
    document.getElementById('recommendation-filter')?.addEventListener('change', (e) => {
        const filter = e.target.value;
        const filtered = filter === 'all' 
            ? allPredictions 
            : allPredictions.filter(p => p.recommendation === filter);
        renderPredictionsTable(filtered);
    });
    
    document.getElementById('ticker-search')?.addEventListener('input', (e) => {
        const search = e.target.value.toUpperCase();
        const filtered = allPredictions.filter(p => 
            p.ticker.toUpperCase().includes(search)
        );
        renderPredictionsTable(filtered);
    });
    
    // Stock search
    document.getElementById('stock-search')?.addEventListener('input', (e) => {
        const search = e.target.value.toUpperCase();
        const filtered = allStocks.filter(s => 
            s.ticker.toUpperCase().includes(search)
        );
        renderStocksTable(filtered);
    });
    
    // News filters
    document.getElementById('sentiment-filter')?.addEventListener('change', (e) => {
        const filter = e.target.value;
        let filtered = allNews;
        if (filter !== 'all') {
            filtered = allNews.filter(a => {
                const sentiment = getSentimentLabel(a.sentiment_score);
                return sentiment.toLowerCase() === filter;
            });
        }
        renderNewsList(filtered);
    });
    
    document.getElementById('news-search')?.addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const filtered = allNews.filter(a => 
            (a.title || '').toLowerCase().includes(search) ||
            (a.summary || '').toLowerCase().includes(search)
        );
        renderNewsList(filtered);
    });
}

// Pipeline
function setupPipeline() {
    const btn = document.getElementById('run-pipeline');
    const status = document.getElementById('pipeline-status');
    
    btn?.addEventListener('click', async () => {
        btn.disabled = true;
        status.textContent = 'Running pipeline...';
        
        try {
            await API.runPipeline();
            
            // Poll for status
            const pollStatus = setInterval(async () => {
                const result = await API.getPipelineStatus();
                status.textContent = result.status || 'Running...';
                
                if (result.status === 'completed' || result.status === 'failed' || result.status === 'idle') {
                    clearInterval(pollStatus);
                    btn.disabled = false;
                    
                    if (result.status === 'completed') {
                        status.textContent = 'Pipeline completed!';
                        loadDashboard(); // Refresh data
                    }
                }
            }, 2000);
            
        } catch (err) {
            console.error('Pipeline failed:', err);
            status.textContent = 'Pipeline failed';
            btn.disabled = false;
        }
    });
}

// Helper Functions
function renderList(containerId, items, mapper) {
    const container = document.getElementById(containerId);
    
    if (!items.length) {
        container.innerHTML = '<p class="loading">No data available</p>';
        return;
    }
    
    container.innerHTML = items.map(item => {
        const data = mapper(item);
        return `
            <div class="list-item clickable-row" onclick="openStockModal('${data.ticker}')">
                <div>
                    <div class="ticker">${data.ticker}</div>
                    <div class="details">${data.details}</div>
                </div>
                <div class="value ${data.valueClass}">${data.value}</div>
            </div>
        `;
    }).join('');
}

function renderNewsGrid(containerId, articles) {
    const container = document.getElementById(containerId);
    
    if (!articles.length) {
        container.innerHTML = '<p class="loading">No news available</p>';
        return;
    }
    
    container.innerHTML = articles.map(a => {
        // Get sentiment score from multiple possible fields
        const sentimentScore = parseFloat(
            a.sentiment_compound || 
            a.sentiment_score || 
            (a.sentiment && a.sentiment.compound) || 
            0
        );
        const sentimentDisplay = getSentimentDisplay(sentimentScore);
        
        return `
            <div class="news-card">
                <div class="headline">${a.title || 'No title'}</div>
                <div class="meta">
                    <span>${a.ticker || 'General'}</span>
                    <span class="sentiment ${sentimentDisplay.color}">
                        ${sentimentDisplay.emoji} ${sentimentDisplay.label}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

function getBadgeClass(recommendation) {
    if (recommendation?.includes('BUY')) return 'buy';
    if (recommendation?.includes('SELL')) return 'sell';
    return 'hold';
}

function getSentimentLabel(score) {
    const s = parseFloat(score) || 0;
    if (s > 0.1) return 'Positive';
    if (s < -0.1) return 'Negative';
    return 'Neutral';
}

function getSentimentDisplay(score) {
    const s = parseFloat(score) || 0;
    
    // Convert -1 to 1 scale to a more intuitive display
    if (s >= 0.5) return { label: 'Very Positive', emoji: '🟢', color: 'positive' };
    if (s >= 0.1) return { label: 'Positive', emoji: '🟢', color: 'positive' };
    if (s <= -0.5) return { label: 'Very Negative', emoji: '🔴', color: 'negative' };
    if (s <= -0.1) return { label: 'Negative', emoji: '🔴', color: 'negative' };
    return { label: 'Neutral', emoji: '⚪', color: 'neutral' };
}

function formatVolume(vol) {
    if (vol >= 1e9) return (vol / 1e9).toFixed(1) + 'B';
    if (vol >= 1e6) return (vol / 1e6).toFixed(1) + 'M';
    if (vol >= 1e3) return (vol / 1e3).toFixed(1) + 'K';
    return vol.toString();
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function showError(message) {
    // Show error in all list containers
    document.querySelectorAll('.list-container, .news-grid, .news-list').forEach(el => {
        el.innerHTML = `<p class="loading" style="color: var(--danger);">${message}</p>`;
    });
}


// Stock Detail Modal
let currentChart = null;
let currentTicker = null;
let currentChartType = 'candlestick';
let currentPeriod = '1y';

async function openStockModal(ticker) {
    currentTicker = ticker.toUpperCase();
    const modal = document.getElementById('stock-modal');
    modal.style.display = 'flex';
    
    // Get company name
    const companyName = typeof getCompanyName === 'function' ? getCompanyName(currentTicker) : currentTicker;
    
    // Update modal title with company name
    document.getElementById('modal-ticker').textContent = `${currentTicker} - ${companyName}`;
    
    // Show loading skeletons
    document.getElementById('modal-price').textContent = 'Loading...';
    document.getElementById('modal-change').textContent = '--';
    document.getElementById('modal-recommendation').textContent = '--';
    document.getElementById('modal-sentiment').textContent = '--';
    
    // Show chart loading
    const chartContainer = document.getElementById('chart-container');
    chartContainer.innerHTML = '<div class="chart-loading">Loading chart data...</div>';
    
    // Show news loading
    const newsContainer = document.getElementById('modal-news');
    newsContainer.innerHTML = '<div class="skeleton-news"></div><div class="skeleton-news"></div><div class="skeleton-news"></div>';
    
    // Load stock data
    try {
        await loadStockDetails(currentTicker);
    } catch (err) {
        console.error('Error loading stock:', err);
        document.getElementById('modal-price').textContent = 'Error';
        chartContainer.innerHTML = `<div class="chart-loading">Failed to load data for ${currentTicker}. Please check the ticker symbol.</div>`;
        newsContainer.innerHTML = `<p class="loading">Could not load data. Ticker "${currentTicker}" may not exist.</p>`;
    }
}

function closeStockModal() {
    const modal = document.getElementById('stock-modal');
    modal.style.display = 'none';
    
    // Cleanup chart
    if (currentChart) {
        currentChart.remove();
        currentChart = null;
    }
}

async function loadStockDetails(ticker) {
    try {
        // Load stock info, prediction, and news in parallel
        const [stockData, predictionData, newsData] = await Promise.all([
            API.getStockByTicker(ticker).catch(err => {
                console.error('Stock data error:', err);
                return { error: err.message };
            }),
            API.getPredictionByTicker(ticker).catch(err => {
                console.error('Prediction data error:', err);
                return { error: err.message };
            }),
            API.getNewsByTicker(ticker).catch(err => {
                console.error('News data error:', err);
                return { error: err.message };
            })
        ]);
        
        // Check if stock exists
        if (stockData.error || !stockData.price) {
            throw new Error(`Stock ${ticker} not found or data unavailable`);
        }
        
        // Update stock info
        const stock = stockData.price || {};
        const prediction = predictionData.prediction || {};
        
        document.getElementById('modal-price').textContent = 
            `$${parseFloat(stock.price || stock.current_price || 0).toFixed(2)}`;
        
        const changePct = parseFloat(stock.change_percent || 0);
        const changeEl = document.getElementById('modal-change');
        changeEl.textContent = `${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%`;
        changeEl.className = `value ${changePct >= 0 ? 'positive' : 'negative'}`;
        
        document.getElementById('modal-recommendation').textContent = 
            prediction.recommendation || 'N/A';
        
        const sentiment = parseFloat(prediction.avg_sentiment || 0);
        const sentimentEl = document.getElementById('modal-sentiment');
        sentimentEl.textContent = `${(sentiment * 100).toFixed(0)}%`;
        sentimentEl.className = `value ${sentiment >= 0 ? 'positive' : 'negative'}`;
        
        // Load chart
        await loadChart(ticker, currentPeriod);
        
        // Load news - if no specific news, get general news
        let articles = newsData.articles || [];
        
        // If no specific news for this ticker, get sector/general news
        if (articles.length === 0) {
            const sector = stock.sector || '';
            const generalNews = await API.getNews();
            
            // Try to find related news by sector or general market
            if (sector && sector !== 'Unknown') {
                articles = (generalNews.articles || [])
                    .filter(a => {
                        const title = (a.title || '').toLowerCase();
                        const sectorLower = sector.toLowerCase();
                        return title.includes(sectorLower) || 
                               title.includes('market') || 
                               title.includes('stock');
                    })
                    .slice(0, 5);
            } else {
                // Just show recent general market news
                articles = (generalNews.articles || []).slice(0, 5);
            }
        }
        
        console.log('News data for', ticker, ':', articles.length, 'articles');
        renderModalNews(articles, ticker);
        
    } catch (err) {
        console.error('Failed to load stock details:', err);
        
        // Show error in UI
        document.getElementById('modal-price').textContent = 'N/A';
        document.getElementById('modal-change').textContent = 'N/A';
        document.getElementById('modal-recommendation').textContent = 'N/A';
        document.getElementById('modal-sentiment').textContent = 'N/A';
        
        const chartContainer = document.getElementById('chart-container');
        chartContainer.innerHTML = `
            <div class="chart-loading" style="color: var(--danger);">
                <p>❌ Failed to load data for ${ticker}</p>
                <p style="font-size: 0.875rem; margin-top: 0.5rem;">
                    ${err.message || 'Stock ticker may not exist or data is unavailable'}
                </p>
            </div>
        `;
        
        const newsContainer = document.getElementById('modal-news');
        newsContainer.innerHTML = '<p class="loading">Unable to load news</p>';
    }
}

async function loadChart(ticker, period) {
    const container = document.getElementById('chart-container');
    container.innerHTML = '<div class="chart-loading">Loading chart...</div>';
    
    try {
        // Check if library is loaded
        if (typeof LightweightCharts === 'undefined') {
            container.innerHTML = '<div class="chart-loading">Chart library not loaded. Please refresh the page.</div>';
            console.error('LightweightCharts is not defined');
            return;
        }
        
        const historyData = await API.getStockHistory(ticker, period);
        
        if (!historyData.data || !historyData.data.length) {
            container.innerHTML = '<div class="chart-loading">No chart data available</div>';
            return;
        }
        
        console.log('Chart data sample:', historyData.data[0]);
        
        // Clear loading
        container.innerHTML = '';
        
        // Create chart
        if (currentChart) {
            try {
                currentChart.remove();
            } catch (e) {
                console.warn('Error removing old chart:', e);
            }
            currentChart = null;
        }
        
        const chartOptions = {
            width: container.clientWidth,
            height: 450,
            layout: {
                background: { color: '#1a1a2e' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: '#2a2a3e' },
                horzLines: { color: '#2a2a3e' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#2a2a3e',
            },
            timeScale: {
                borderColor: '#2a2a3e',
                timeVisible: true,
                secondsVisible: false,
            },
            localization: {
                priceFormatter: (price) => '$' + price.toFixed(2),
            },
        };
        
        currentChart = LightweightCharts.createChart(container, chartOptions);
        
        // Convert dates to proper format (YYYY-MM-DD)
        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        // Add series based on chart type
        if (currentChartType === 'line') {
            const lineSeries = currentChart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
                priceFormat: {
                    type: 'price',
                    precision: 2,
                    minMove: 0.01,
                },
            });
            
            const lineData = historyData.data.map(d => ({
                time: formatDate(d.date),
                value: parseFloat(d.close)
            }));
            
            lineSeries.setData(lineData);
        } else {
            const candlestickSeries = currentChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
                priceFormat: {
                    type: 'price',
                    precision: 2,
                    minMove: 0.01,
                },
            });
            
            const candleData = historyData.data.map(d => ({
                time: formatDate(d.date),
                open: parseFloat(d.open),
                high: parseFloat(d.high),
                low: parseFloat(d.low),
                close: parseFloat(d.close)
            }));
            
            candlestickSeries.setData(candleData);
            
            // Add volume histogram
            const volumeSeries = currentChart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '',
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
            
            const volumeData = historyData.data.map(d => ({
                time: formatDate(d.date),
                value: parseFloat(d.volume),
                color: d.close >= d.open ? '#26a69a80' : '#ef535080'
            }));
            
            volumeSeries.setData(volumeData);
        }
        
        currentChart.timeScale().fitContent();
        
        // Handle resize
        const resizeHandler = () => {
            if (currentChart && container.clientWidth > 0) {
                currentChart.applyOptions({ 
                    width: container.clientWidth 
                });
            }
        };
        
        window.removeEventListener('resize', resizeHandler);
        window.addEventListener('resize', resizeHandler);
        
    } catch (err) {
        console.error('Failed to load chart:', err);
        container.innerHTML = `<div class="chart-loading">Failed to load chart: ${err.message}</div>`;
    }
}

function switchChartType(type) {
    currentChartType = type;
    
    // Update button states
    document.querySelectorAll('.chart-type-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === type);
    });
    
    // Reload chart
    if (currentTicker) {
        loadChart(currentTicker, currentPeriod);
    }
}

function changePeriod(period) {
    currentPeriod = period;
    
    // Update button states
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.period === period);
    });
    
    // Reload chart
    if (currentTicker) {
        loadChart(currentTicker, currentPeriod);
    }
}

function renderModalNews(articles, ticker) {
    const container = document.getElementById('modal-news');
    
    if (!articles || !articles.length) {
        container.innerHTML = `
            <p class="loading">No specific news found for ${ticker || 'this stock'}.</p>
            <p class="loading" style="margin-top: 0.5rem; font-size: 0.875rem;">
                The prediction is based on general market and sector news.
            </p>
        `;
        return;
    }
    
    // Check if these are direct ticker news or related news
    const hasDirectNews = articles.some(a => 
        (a.ticker || '').toUpperCase() === (ticker || '').toUpperCase()
    );
    
    const newsType = hasDirectNews ? 
        `📰 Recent News for ${ticker}` : 
        `📰 Related Market News (No direct ${ticker} news available)`;
    
    // Update section title
    const sectionTitle = container.parentElement.querySelector('h3');
    if (sectionTitle) {
        sectionTitle.textContent = newsType;
    }
    
    container.innerHTML = articles.slice(0, 5).map(a => {
        // Get sentiment score from multiple possible fields
        const sentimentScore = parseFloat(
            a.sentiment_compound || 
            a.sentiment_score || 
            (a.sentiment && a.sentiment.compound) || 
            0
        );
        
        const sentimentDisplay = getSentimentDisplay(sentimentScore);
        const publishedDate = a.published_at || a.published_date || a.date || '';
        const articleTicker = a.ticker || 'General';
        
        return `
            <div class="modal-news-item">
                <div class="headline">${a.title || 'No title'}</div>
                <div class="meta">
                    <span class="sentiment ${sentimentDisplay.color}">
                        ${sentimentDisplay.emoji} ${sentimentDisplay.label}
                    </span>
                    ${articleTicker !== 'General' ? `<span>Ticker: ${articleTicker}</span>` : ''}
                    ${publishedDate ? `<span>${formatDate(publishedDate)}</span>` : ''}
                    ${a.source ? `<span>${a.source}</span>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('stock-modal');
    if (event.target === modal) {
        closeStockModal();
    }
}


// Global Search Feature
document.getElementById('global-search')?.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
        const searchTerm = e.target.value.trim();
        if (searchTerm) {
            // Use smart lookup to find ticker
            const ticker = findTicker(searchTerm);
            
            console.log(`Search: "${searchTerm}" → Ticker: "${ticker}"`);
            
            // Open the stock modal
            openStockModal(ticker);
            
            // Clear search box
            e.target.value = '';
        }
    }
});

// Add autocomplete suggestions
let searchTimeout;
document.getElementById('global-search')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const searchTerm = e.target.value.trim().toLowerCase();
    
    if (searchTerm.length < 2) return;
    
    // Debounce search
    searchTimeout = setTimeout(() => {
        // Find matching companies
        const matches = [];
        for (const [name, ticker] of Object.entries(STOCK_LOOKUP)) {
            if (name.includes(searchTerm)) {
                matches.push({ name, ticker });
                if (matches.length >= 5) break;
            }
        }
        
        // Could show dropdown here in future
        if (matches.length > 0) {
            console.log('Suggestions:', matches);
        }
    }, 300);
});
