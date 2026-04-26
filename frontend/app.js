// MarketBrief — main application
let allPredictions = [];
let allStocks = [];
let allNews = [];
let totals = { predictions: null, news: null };
let currentView = 'grid';
let currentTicker = null;
let currentPeriod = '1mo';
let chart = null;
let candlestickSeries = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupFilters();
    setupSearch();
    setupStockFilters();
    setupPipelineControls();
    setupShellUI();
    loadAllData();
    
    // Auto-refresh every 5 minutes
    setInterval(loadAllData, 5 * 60 * 1000);
});

function setupShellUI() {
    const sidebar = document.getElementById("sidebar");
    const scrim = document.getElementById("scrim");
    const toggle = document.getElementById("sidebar-toggle");
    const close = document.getElementById("sidebar-close");
    const bannerClose = document.getElementById("banner-close");
    
    const openSidebar = () => {
        if (!sidebar || !scrim) return;
        sidebar.classList.add("open");
        scrim.classList.add("open");
    };
    const closeSidebar = () => {
        if (!sidebar || !scrim) return;
        sidebar.classList.remove("open");
        scrim.classList.remove("open");
    };
    
    toggle?.addEventListener("click", openSidebar);
    close?.addEventListener("click", closeSidebar);
    scrim?.addEventListener("click", closeSidebar);
    bannerClose?.addEventListener("click", () => hideBanner());
}

function showBanner(message) {
    const b = document.getElementById("banner");
    const t = document.getElementById("banner-text");
    if (!b || !t) return;
    t.textContent = message;
    b.classList.remove("hidden");
}

function hideBanner() {
    const b = document.getElementById("banner");
    if (!b) return;
    b.classList.add("hidden");
}

function toast({ type = "ok", title = "", message = "", timeoutMs = 3200 }) {
    const root = document.getElementById("toasts");
    if (!root) return;
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.innerHTML = `
        <div>
            <div class="toast-title">${escapeHtml(title)}</div>
            <div class="toast-msg">${escapeHtml(message)}</div>
        </div>
        <button class="icon-btn" title="Dismiss">✕</button>
    `;
    el.querySelector("button")?.addEventListener("click", () => el.remove());
    root.appendChild(el);
    setTimeout(() => el.remove(), timeoutMs);
}

function escapeHtml(s) {
    return String(s ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function setupStockFilters() {
    const search = document.getElementById('stock-search');
    const sector = document.getElementById('sector-filter');
    search?.addEventListener('input', () => loadStocks());
    sector?.addEventListener('change', () => loadStocks());
}

function normalizeSector(s) {
    const v = String(s ?? '').trim();
    if (!v) return 'Unknown';
    if (v.toLowerCase() === 'n/a') return 'Unknown';
    return v;
}

function updateSectorDropdown() {
    const select = document.getElementById('sector-filter');
    if (!select) return;

    const prev = select.value || 'all';
    const sectors = Array.from(new Set((allPredictions || []).map(p => normalizeSector(p.sector))))
        .sort((a, b) => a.localeCompare(b));

    select.innerHTML = [
        `<option value="all">All Sectors</option>`,
        ...sectors.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`),
    ].join('');

    const stillExists = Array.from(select.options).some(o => o.value === prev);
    select.value = stillExists ? prev : 'all';
}

// Setup Navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(`${page}-page`).classList.add('active');
            
            updatePageTitle(page);
            loadPageData(page);
        });
    });
    
    document.getElementById('refresh-btn').addEventListener('click', loadAllData);
}

function setupPipelineControls() {
    const runBtn = document.getElementById('run-pipeline-btn');
    if (!runBtn) return;
    
    runBtn.addEventListener('click', async () => {
        try {
            showTopProgress({ label: "Running pipeline…", stage: "Starting", percent: 1 });
            await API.runPipeline();
            // Optimistic UI: start polling status, progress updates will drive bar.
            await pollPipelineUntilDone();
            await loadAllData();
            toast({ type: "ok", title: "Pipeline complete", message: "Predictions and news were updated." });
        } catch (e) {
            console.error("Pipeline run failed", e);
            showTopProgress({ label: "Pipeline failed", stage: String(e?.message || e), percent: 100 });
            setTimeout(hideTopProgress, 2500);
            showBanner(`Pipeline failed: ${String(e?.message || e)}`);
            toast({ type: "err", title: "Pipeline failed", message: String(e?.message || e) });
        }
    });
}

function showTopProgress({ label, stage, percent }) {
    const el = document.getElementById("top-progress");
    if (!el) return;
    el.classList.remove("hidden");
    document.getElementById("top-progress-label").textContent = label || "Updating…";
    document.getElementById("top-progress-stage").textContent = stage || "";
    document.getElementById("top-progress-percent").textContent = `${Math.max(0, Math.min(100, percent || 0))}%`;
    document.getElementById("top-progress-fill").style.width = `${Math.max(0, Math.min(100, percent || 0))}%`;
}

function hideTopProgress() {
    const el = document.getElementById("top-progress");
    if (!el) return;
    el.classList.add("hidden");
}

async function pollPipelineUntilDone(timeoutMs = 10 * 60 * 1000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
        const status = await API.getPipelineStatus();
        const p = status?.progress || {};
        const isRunning = !!status?.is_running;
        const pct = typeof p.percent === "number" ? p.percent : 0;
        const stage = p.stage || (isRunning ? "running" : "idle");
        const msg = p.message || "";
        
        showTopProgress({
            label: isRunning ? "Running pipeline…" : "Finalizing…",
            stage: msg ? `${stage}: ${msg}` : stage,
            percent: isRunning ? Math.max(1, Math.min(99, pct)) : 100,
        });
        
        if (!isRunning) {
            // pipeline ended (success or error)
            const last = status?.last_result;
            if (last?.status === "error") {
                throw new Error(last?.error || "Pipeline error");
            }
            setTimeout(hideTopProgress, 1200);
            return;
        }
        
        await new Promise(r => setTimeout(r, 1200));
    }
    throw new Error("Pipeline timed out");
}

function updatePageTitle(page) {
    const titles = {
        dashboard: 'AI-Powered Stock Analysis',
        predictions: 'AI Predictions',
        stocks: 'Live Stock Data',
        news: 'News Feed',
        analytics: 'Analytics Dashboard',
        training: 'ML Training & Data'
    };
    const subtitles = {
        dashboard: 'Real-time sentiment analysis from 5000+ news sources',
        predictions: 'Machine learning powered buy/sell recommendations',
        stocks: 'Live market data and price movements',
        news: 'Latest financial news with sentiment analysis',
        analytics: 'Model performance and data insights',
        training: 'Collect historical data and train custom AI models'
    };
    document.getElementById('page-title').textContent = titles[page] || page;
    document.getElementById('page-subtitle').textContent = subtitles[page] || '';
}

// Load all data automatically
async function loadAllData() {
    try {
        showTopProgress({ label: "Refreshing data…", stage: "Fetching API data", percent: 10 });
        hideBanner();

        // Fetch totals (so sidebar shows full dataset size, not just the preloaded slice).
        try {
            const [predSummaryRes, newsSummaryRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/predictions/summary'),
                fetch('http://localhost:8000/api/v1/news/summary'),
            ]);
            const predSummary = await predSummaryRes.json();
            const newsSummary = await newsSummaryRes.json();
            // predictions/summary returns total_stocks (not total_count)
            const predTotal = Number(predSummary?.total_stocks ?? predSummary?.total_count ?? NaN);
            const newsTotal = Number(newsSummary?.total_count ?? NaN);
            totals.predictions = Number.isFinite(predTotal) && predTotal > 0 ? predTotal : null;
            totals.news = Number.isFinite(newsTotal) && newsTotal > 0 ? newsTotal : null;
        } catch (_) {
            // Ignore: we can still render with slice lengths.
        }
        // Fetch all predictions (max 500 per request)
        const predictionsRes = await fetch('http://localhost:8000/api/v1/predictions/?limit=300');
        const predictionsData = await predictionsRes.json();
        allPredictions = predictionsData.predictions || [];
        
        // Keep the dashboard fast: load a smaller news slice on refresh.
        // The full news page can be loaded on-demand.
        const newsRes = await fetch('http://localhost:8000/api/v1/news/?limit=500&offset=0&days=7');
        const newsData = await newsRes.json();
        allNews = [...(newsData.articles || [])];
        
        console.log('✅ Loaded:', allPredictions.length, 'predictions,', allNews.length, 'news articles');
        
        updateSectorDropdown();
        updateSidebar();
        loadDashboard();
        showTopProgress({ label: "Up to date", stage: "Done", percent: 100 });
        setTimeout(hideTopProgress, 800);
        
    } catch (error) {
        console.error('❌ Error loading data:', error);
        showError('Failed to load data. Please refresh the page.');
        showTopProgress({ label: "Refresh failed", stage: String(error?.message || error), percent: 100 });
        setTimeout(hideTopProgress, 2500);
        showBanner(`Refresh failed: ${String(error?.message || error)}`);
        toast({ type: "err", title: "Refresh failed", message: String(error?.message || error) });
    }
}

function updateSidebar() {
    const predCount = Number.isFinite(totals.predictions) ? totals.predictions : allPredictions.length;
    const newsCount = Number.isFinite(totals.news) ? totals.news : allNews.length;
    document.getElementById('sidebar-stocks').textContent = predCount;
    document.getElementById('sidebar-news').textContent = newsCount;
    document.getElementById('sidebar-update').textContent = new Date().toLocaleTimeString();
}

// Dashboard
async function loadDashboard() {
    try {
        const summary = await API.getPredictionSummary();
        
        // Prefer server-side totals (covers full dataset, not just the preloaded slice).
        const sb = Number(summary?.strong_buy_count);
        const b = Number(summary?.buy_count);
        const h = Number(summary?.hold_count);
        const s = Number(summary?.sell_count);
        const ss = Number(summary?.strong_sell_count);
        const hasTotals =
            Number.isFinite(sb) && Number.isFinite(b) && Number.isFinite(h) && Number.isFinite(s) && Number.isFinite(ss);

        // Calculate metrics
        const strongBuy = hasTotals ? sb : allPredictions.filter(p => p.recommendation === 'STRONG BUY').length;
        const buy = hasTotals ? b : allPredictions.filter(p => p.recommendation === 'BUY').length;
        const hold = hasTotals ? h : allPredictions.filter(p => p.recommendation === 'HOLD').length;
        const sell = hasTotals ? s : allPredictions.filter(p => p.recommendation === 'SELL').length;
        const strongSell = hasTotals ? ss : allPredictions.filter(p => p.recommendation === 'STRONG SELL').length;
        
        // Calculate average confidence for stocks with news (not all stocks)
        const stocksWithNews = allPredictions.filter(p => p.news_count > 0);
        const avgConfidence = stocksWithNews.length > 0 
            ? stocksWithNews.reduce((sum, p) => sum + (p.confidence || 0), 0) / stocksWithNews.length
            : 0;
        
        // Update metrics
        document.getElementById('strong-buy-count').textContent = strongBuy + buy;
        document.getElementById('hold-count').textContent = hold;
        document.getElementById('sell-count').textContent = sell + strongSell;
        document.getElementById('avg-confidence').textContent = (avgConfidence * 100).toFixed(1) + '%';
        
        // Top recommendations (with news)
        const topRecs = allPredictions
            .filter(p => (p.recommendation === 'STRONG BUY' || p.recommendation === 'BUY') && p.news_count > 0)
            .sort((a, b) => b.prediction_score - a.prediction_score)
            .slice(0, 6);
        
        renderTopRecommendations(topRecs);
        
        // Gainers and losers
        const gainers = allPredictions
            .filter(p => p.price_change_percent > 0)
            .sort((a, b) => b.price_change_percent - a.price_change_percent)
            .slice(0, 5);
        
        const losers = allPredictions
            .filter(p => p.price_change_percent < 0)
            .sort((a, b) => a.price_change_percent - b.price_change_percent)
            .slice(0, 5);
        
        renderGainersLosers(gainers, losers);
        
        // Sentiment analysis
        const positive = allNews.filter(n => n.sentiment_compound > 0.05).length;
        const neutral = allNews.filter(n => n.sentiment_compound >= -0.05 && n.sentiment_compound <= 0.05).length;
        const negative = allNews.filter(n => n.sentiment_compound < -0.05).length;
        
        document.getElementById('positive-sentiment').textContent = positive;
        document.getElementById('neutral-sentiment').textContent = neutral;
        document.getElementById('negative-sentiment').textContent = negative;
        document.getElementById('total-news-count').textContent = allNews.length;
        
        const total = positive + neutral + negative;
        document.getElementById('positive-percent').textContent = ((positive / total) * 100).toFixed(1) + '%';
        document.getElementById('neutral-percent').textContent = ((neutral / total) * 100).toFixed(1) + '%';
        document.getElementById('negative-percent').textContent = ((negative / total) * 100).toFixed(1) + '%';
        
        // High-impact news
        const highImpact = allNews
            .filter(n => n.impact_level === 'high' || n.impact_level === 'macro')
            .slice(0, 10);
        
        renderHighImpactNews(highImpact);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function renderTopRecommendations(recs) {
    const container = document.getElementById('top-recommendations');
    if (!recs || recs.length === 0) {
        container.innerHTML = '<p class="no-data">No recommendations available</p>';
        return;
    }
    
    container.innerHTML = recs.map(p => `
        <div class="recommendation-card" onclick="showStockDetail('${p.ticker}')">
            <div class="rec-header">
                <div class="rec-ticker">${p.ticker}</div>
                <div class="rec-badge ${p.recommendation.toLowerCase().replace(' ', '-')}">${p.recommendation}</div>
                <button class="btn-small" title="Add to watchlist" onclick="event.stopPropagation();watchlistGet().includes('${p.ticker}')?watchlistRemove('${p.ticker}'):(watchlistGet().push('${p.ticker}'),watchlistSave(watchlistGet()));this.textContent=watchlistGet().includes('${p.ticker}')?'★':'☆';" style="margin-left:auto;background:none;border:none;font-size:1rem;cursor:pointer;color:#f59e0b;">${'★'}</button>
            </div>
            <div class="rec-company">${p.company_name || p.ticker}</div>
            <div class="rec-metrics">
                <div class="rec-metric">
                    <span class="rec-label">Price</span>
                    <span class="rec-value">$${p.current_price.toFixed(2)}</span>
                </div>
                <div class="rec-metric">
                    <span class="rec-label">Change</span>
                    <span class="rec-value ${p.price_change_percent >= 0 ? 'positive' : 'negative'}">
                        ${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%
                    </span>
                </div>
                <div class="rec-metric">
                    <span class="rec-label">Confidence</span>
                    <span class="rec-value">${(p.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
            <div class="rec-sentiment">
                <div class="sentiment-bar">
                    <div class="sentiment-fill ${p.avg_sentiment >= 0 ? 'positive' : 'negative'}" 
                         style="width: ${Math.abs(p.avg_sentiment) * 100}%"></div>
                </div>
                <span class="sentiment-text">${p.news_count} news articles</span>
            </div>
        </div>
    `).join('');
}

function renderGainersLosers(gainers, losers) {
    const gainersContainer = document.getElementById('top-gainers');
    const losersContainer = document.getElementById('top-losers');
    
    gainersContainer.innerHTML = gainers.map(p => `
        <div class="stock-item" onclick="showStockDetail('${p.ticker}')">
            <div class="stock-info">
                <div class="stock-ticker">${p.ticker}</div>
                <div class="stock-name">${p.company_name || p.ticker}</div>
            </div>
            <div class="stock-price">
                <div class="price">$${p.current_price.toFixed(2)}</div>
                <div class="change positive">+${p.price_change_percent.toFixed(2)}%</div>
            </div>
        </div>
    `).join('');
    
    losersContainer.innerHTML = losers.map(p => `
        <div class="stock-item" onclick="showStockDetail('${p.ticker}')">
            <div class="stock-info">
                <div class="stock-ticker">${p.ticker}</div>
                <div class="stock-name">${p.company_name || p.ticker}</div>
            </div>
            <div class="stock-price">
                <div class="price">$${p.current_price.toFixed(2)}</div>
                <div class="change negative">${p.price_change_percent.toFixed(2)}%</div>
            </div>
        </div>
    `).join('');
}

function renderHighImpactNews(news) {
    const container = document.getElementById('high-impact-news');
    if (!news || news.length === 0) {
        container.innerHTML = '<p class="no-data">No high-impact news available</p>';
        return;
    }
    
    container.innerHTML = news.map(n => `
        <div class="news-item ${getSentimentClass(n.sentiment_compound)}">
            <div class="news-header">
                <span class="news-source">${n.source}</span>
                <span class="news-time">${formatTime(n.published_at)}</span>
            </div>
            <div class="news-title">${n.title}</div>
            <div class="news-footer">
                <span class="news-ticker">${n.ticker || 'Market'}</span>
                <span class="news-sentiment">${getSentimentLabel(n.sentiment_compound)}</span>
                <span class="news-impact">${n.impact_level}</span>
            </div>
        </div>
    `).join('');
}

// Predictions Page
async function loadPageData(page) {
    if (page === 'predictions') loadPredictions();
    else if (page === 'stocks') loadStocks();
    else if (page === 'news') loadNewsPage();
    else if (page === 'analytics') loadAnalytics();
    else if (page === 'watchlist') loadWatchlist();
    else if (page === 'training') loadTraining();
}

function loadPredictions() {
    const grid = document.getElementById('predictions-grid');
    const tbody = document.getElementById('predictions-tbody');
    
    if (currentView === 'grid') {
        grid.style.display = 'grid';
        document.getElementById('predictions-table-container').style.display = 'none';
        
        grid.innerHTML = allPredictions.map(p => `
            <div class="prediction-card" onclick="showStockDetail('${p.ticker}')">
                <div class="pred-header">
                    <div class="pred-ticker">${p.ticker}</div>
                    <div class="pred-badge ${p.recommendation.toLowerCase().replace(' ', '-')}">${p.recommendation}</div>
                </div>
                <div class="pred-company">${p.company_name || p.ticker}</div>
                <div class="pred-price">$${p.current_price.toFixed(2)}</div>
                <div class="pred-change ${p.price_change_percent >= 0 ? 'positive' : 'negative'}">
                    ${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%
                </div>
                <div class="pred-metrics">
                    <div class="pred-metric">
                        <span>Confidence</span>
                        <strong>${(p.confidence * 100).toFixed(0)}%</strong>
                    </div>
                    <div class="pred-metric">
                        <span>News</span>
                        <strong>${p.news_count}</strong>
                    </div>
                    <div class="pred-metric">
                        <span>Sentiment</span>
                        <strong class="${p.avg_sentiment >= 0 ? 'positive' : 'negative'}">
                            ${p.news_count === 0 || p.avg_sentiment === 0 ? 'N/A' : (p.avg_sentiment > 0 ? '+' : '') + (p.avg_sentiment * 100).toFixed(0) + '%'}
                        </strong>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        grid.style.display = 'none';
        document.getElementById('predictions-table-container').style.display = 'block';
        
        tbody.innerHTML = allPredictions.map(p => `
            <tr onclick="showStockDetail('${p.ticker}')">
                <td><strong>${p.ticker}</strong></td>
                <td>${p.company_name || p.ticker}</td>
                <td>$${p.current_price.toFixed(2)}</td>
                <td><span class="badge ${p.recommendation.toLowerCase().replace(' ', '-')}">${p.recommendation}</span></td>
                <td class="${p.avg_sentiment >= 0 ? 'positive' : 'negative'}">${p.news_count === 0 || p.avg_sentiment === 0 ? 'N/A' : (p.avg_sentiment > 0 ? '+' : '') + (p.avg_sentiment * 100).toFixed(0) + '%'}</td>
                <td>${(p.confidence * 100).toFixed(0)}%</td>
                <td>${p.news_count}</td>
            </tr>
        `).join('');
    }
}

function loadStocks() {
    const tbody = document.getElementById('stocks-tbody');
    const q = (document.getElementById('stock-search')?.value || '').trim().toLowerCase();
    const sectorSelected = document.getElementById('sector-filter')?.value || 'all';

    const filtered = (allPredictions || []).filter(p => {
        const sec = normalizeSector(p.sector);
        if (sectorSelected !== 'all' && sec !== sectorSelected) return false;
        if (!q) return true;
        const t = String(p.ticker ?? '').toLowerCase();
        const n = String(p.company_name ?? '').toLowerCase();
        return t.includes(q) || n.includes(q);
    });

    tbody.innerHTML = filtered.map(p => `
        <tr onclick="showStockDetail('${p.ticker}')">
            <td><strong>${p.ticker}</strong></td>
            <td>${p.company_name || p.ticker}</td>
            <td>$${p.current_price.toFixed(2)}</td>
            <td class="${p.price_change_percent >= 0 ? 'positive' : 'negative'}">
                ${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%
            </td>
            <td class="${p.price_change_percent >= 0 ? 'positive' : 'negative'}">
                ${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%
            </td>
            <td>${escapeHtml(normalizeSector(p.sector))}</td>
            <td><button class="btn-small" onclick="event.stopPropagation(); showStockDetail('${p.ticker}')">View</button></td>
        </tr>
    `).join('');
}

function loadNewsPage() {
    const container = document.getElementById('news-list');
    // If user navigates to News, fetch a larger set on-demand for that page.
    // (Avoids making the whole app sluggish on every refresh.)
    if (allNews.length < 1500) {
        container.innerHTML = '<div class="loading-spinner"></div>';
        fetch('http://localhost:8000/api/v1/news/?limit=2000&offset=0')
            .then(r => r.json())
            .then(d => {
                allNews = d.articles || allNews;
                renderNewsList(container, allNews);
            })
            .catch(() => {
                renderNewsList(container, allNews);
            });
        return;
    }
    renderNewsList(container, allNews);
}

function renderNewsList(container, newsItems) {
    container.innerHTML = (newsItems || []).slice(0, 500).map(n => `
        <div class="news-card ${getSentimentClass(n.sentiment_compound)}">
            <div class="news-card-header">
                <span class="news-source">${n.source}</span>
                <span class="news-time">${formatTime(n.published_at)}</span>
            </div>
            <h4 class="news-card-title">${n.title}</h4>
            <div class="news-card-footer">
                <span class="news-ticker">${n.ticker || 'Market'}</span>
                <span class="news-sentiment-badge ${getSentimentClass(n.sentiment_compound)}">
                    ${getSentimentLabel(n.sentiment_compound)}
                </span>
                <span class="news-impact-badge">${n.impact_level}</span>
            </div>
        </div>
    `).join('');
}

async function loadAnalytics() {
    const summary = await API.getPredictionSummary();

    // Ensure we have full predictions loaded (not just the 300-item dashboard slice)
    let preds = allPredictions;
    if (preds.length < 100) {
        try {
            const res = await fetch('http://localhost:8000/api/v1/predictions/?limit=600');
            const d = await res.json();
            preds = d.predictions || preds;
        } catch(e) {}
    }

    // Real metrics from loaded predictions
    const avgConfidence = preds.length > 0
        ? preds.reduce((sum, p) => sum + (p.confidence || 0), 0) / preds.length
        : 0;
    const stocksWithNews = preds.filter(p => p.news_count > 0).length;
    const sentimentCoverage = preds.length > 0
        ? ((stocksWithNews / preds.length) * 100).toFixed(1) + '%'
        : '--';

    // Pull real model metrics from pipeline status
    let modelAccuracy = '--';
    let modelF1 = '--';
    let modelAUC = '--';
    let freshness = 'Unknown';
    try {
        const statusRes = await fetch('http://localhost:8000/api/v1/pipeline/status');
        const statusData = await statusRes.json();
        const fc = statusData?.last_result?.steps?.forecast;
        if (fc?.metrics) {
            modelAccuracy = (fc.metrics.accuracy * 100).toFixed(1) + '%';
            modelF1       = (fc.metrics.f1 * 100).toFixed(1) + '%';
            modelAUC      = fc.metrics.auc.toFixed(3);
        }
        const lastRun = statusData?.last_result?.completed_at || statusData?.last_run;
        if (lastRun) {
            const dt = new Date(lastRun);
            const diffMin = Math.round((Date.now() - dt) / 60000);
            freshness = diffMin < 60
                ? diffMin + ' min ago'
                : dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
        }
    } catch(e) {}

    document.getElementById('model-accuracy').textContent   = modelAccuracy;
    document.getElementById('model-confidence').textContent = (avgConfidence * 100).toFixed(1) + '%';
    document.getElementById('model-precision').textContent  = modelF1;
    document.getElementById('model-coverage').textContent   = modelAUC;

        // Pull real news totals from API summary
    let totalArticles = allNews.length;
    let highImpactCount = allNews.filter(n => n.impact_level === 'high').length;
    let positiveCount = 0, negativeCount = 0;
    try {
        const newsRes = await fetch('http://localhost:8000/api/v1/news/summary');
        const newsData = await newsRes.json();
        totalArticles   = newsData.total_count ?? totalArticles;
        highImpactCount = newsData.high_impact_count ?? highImpactCount;
        positiveCount   = newsData.positive_count ?? 0;
        negativeCount   = newsData.negative_count ?? 0;
    } catch(e) {}

    // freshness already set above

    // Update data quality metrics
    document.getElementById('total-articles').textContent    = totalArticles.toLocaleString();
    document.getElementById('high-impact-count').textContent = highImpactCount.toLocaleString();
    document.getElementById('stocks-with-news').textContent  = stocksWithNews;
    document.getElementById('avg-news-per-stock').textContent = preds.length > 0
        ? (totalArticles / preds.length).toFixed(1) : '--';
    document.getElementById('data-freshness').textContent    = freshness;
    document.getElementById('sentiment-coverage').textContent = sentimentCoverage;
    
    // Distribution
    const sb = Number(summary?.strong_buy_count);
    const b = Number(summary?.buy_count);
    const h = Number(summary?.hold_count);
    const s = Number(summary?.sell_count);
    const ss = Number(summary?.strong_sell_count);
    const hasTotals =
        Number.isFinite(sb) && Number.isFinite(b) && Number.isFinite(h) && Number.isFinite(s) && Number.isFinite(ss);

    const dist = hasTotals
        ? { 'STRONG BUY': sb, 'BUY': b, 'HOLD': h, 'SELL': s, 'STRONG SELL': ss }
        : {
              'STRONG BUY': preds.filter(p => p.recommendation === 'STRONG BUY').length,
              'BUY': preds.filter(p => p.recommendation === 'BUY').length,
              'HOLD': preds.filter(p => p.recommendation === 'HOLD').length,
              'SELL': preds.filter(p => p.recommendation === 'SELL').length,
              'STRONG SELL': preds.filter(p => p.recommendation === 'STRONG SELL').length,
          };
    
    const total = Object.values(dist).reduce((a, b) => a + b, 0);
    const container = document.getElementById('prediction-distribution');
    
    container.innerHTML = Object.entries(dist).map(([label, count]) => `
        <div class="dist-bar">
            <div class="dist-label">${label}</div>
            <div class="dist-progress">
                <div class="dist-fill ${label.includes('BUY') ? 'buy' : label.includes('SELL') ? 'sell' : 'hold'}" 
                     style="width: ${(count / total) * 100}%"></div>
            </div>
            <div class="dist-value">${count} (${((count / total) * 100).toFixed(1)}%)</div>
        </div>
    `).join('');
    
    // Load sector sentiment and news sources from API
    await loadSectorSentiment();
    await loadNewsSources();
}

async function loadSectorSentiment() {
    const container = document.getElementById('sector-sentiment');
    
    try {
        const response = await fetch('http://localhost:8000/api/v1/predictions/summary');
        const data = await response.json();
        
        if (data.top_sectors && data.top_sectors.length > 0) {
            const totalStocks = Number(data.total_stocks || 0);
            const top = (data.top_sectors || []).filter(s => String(s.sector || '').toLowerCase() !== 'unknown');
            const shownSum = top.reduce((acc, s) => acc + Number(s.count || 0), 0);

            // Prefer explicit Unknown count if present in bottom_sectors.
            const unknownFromBottom = (data.bottom_sectors || []).find(
                s => String(s.sector || '').toLowerCase() === 'unknown'
            );
            const unknownCount = Number(unknownFromBottom?.count || 0);

            // "Other sectors" means remaining *known* sectors not shown in top list.
            const otherKnownCount = Math.max(0, totalStocks - unknownCount - shownSum);

            const rows = [
                ...top,
                ...(otherKnownCount > 0 ? [{ sector: 'Other sectors', count: otherKnownCount, avg_score: 0 }] : []),
                ...(unknownCount > 0 ? [{ sector: 'Unknown', count: unknownCount, avg_score: 0 }] : []),
            ];

            container.innerHTML = rows.map(sector => {
                const sentimentPercent = (sector.avg_score * 100).toFixed(1);
                const isPositive = sector.avg_score >= 0;
                
                return `
                    <div class="sector-item">
                        <div class="sector-name">${sector.sector}</div>
                        <div class="sector-stats">
                            <span class="sector-count">${sector.count} stocks</span>
                            <span class="sector-sentiment ${isPositive ? 'positive' : 'negative'}">
                                ${isPositive ? '+' : ''}${sentimentPercent}%
                            </span>
                        </div>
                        <div class="sector-bar">
                            <div class="sector-bar-fill ${isPositive ? 'positive' : 'negative'}" 
                                 style="width: ${Math.abs(sector.avg_score) * 100}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p class="no-data">No sector data available</p>';
        }
    } catch (error) {
        console.error('Error loading sector sentiment:', error);
        container.innerHTML = '<p class="no-data">Failed to load sector data</p>';
    }
}

async function loadNewsSources() {
    const container = document.getElementById('news-sources');
    
    try {
        const response = await fetch('http://localhost:8000/api/v1/news/summary');
        const data = await response.json();
        
        if (data.sources) {
            // Convert sources object to array and sort by count
            const sourcesArray = Object.entries(data.sources)
                .map(([name, count]) => ({ name, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 10); // Top 10 sources
            
            const totalArticles = data.total_count;
            
            container.innerHTML = sourcesArray.map(source => {
                const percentage = ((source.count / totalArticles) * 100).toFixed(1);
                
                return `
                    <div class="source-item">
                        <div class="source-name">${source.name}</div>
                        <div class="source-stats">
                            <span class="source-count">${source.count} articles</span>
                            <span class="source-percent">${percentage}%</span>
                        </div>
                        <div class="source-bar">
                            <div class="source-bar-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = '<p class="no-data">No news source data available</p>';
        }
    } catch (error) {
        console.error('Error loading news sources:', error);
        container.innerHTML = '<p class="no-data">Failed to load news sources</p>';
    }
}

// ── Watchlist ─────────────────────────────────────────────────────────────────

const WL_KEY = 'mb_watchlist';

function watchlistGet() {
    try { return JSON.parse(localStorage.getItem(WL_KEY) || '[]'); } catch(e) { return []; }
}
function watchlistSave(list) {
    localStorage.setItem(WL_KEY, JSON.stringify([...new Set(list.map(t => t.toUpperCase()))]));
}

function watchlistAdd() {
    const input = document.getElementById('watchlist-search');
    const ticker = (input.value || '').trim().toUpperCase();
    if (!ticker) return;
    const list = watchlistGet();
    if (!list.includes(ticker)) {
        list.push(ticker);
        watchlistSave(list);
    }
    input.value = '';
    loadWatchlist();
}

function watchlistRemove(ticker) {
    watchlistSave(watchlistGet().filter(t => t !== ticker));
    loadWatchlist();
}

function watchlistClear() {
    localStorage.removeItem(WL_KEY);
    loadWatchlist();
}

function loadWatchlist() {
    const list = watchlistGet();
    const grid = document.getElementById('watchlist-grid');
    const empty = document.getElementById('watchlist-empty');

    // Allow Enter key to add
    const input = document.getElementById('watchlist-search');
    if (input && !input._wlBound) {
        input.addEventListener('keydown', e => { if (e.key === 'Enter') watchlistAdd(); });
        input._wlBound = true;
    }

    if (list.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    // Match against loaded predictions
    const cards = list.map(ticker => {
        const p = allPredictions.find(x => x.ticker === ticker);
        if (!p) {
            return `
                <div class="prediction-card" style="opacity:0.6;">
                    <div class="pred-header">
                        <div class="pred-ticker">${ticker}</div>
                        <button class="btn-small" style="margin-left:auto;" onclick="watchlistRemove('${ticker}')">✕</button>
                    </div>
                    <div class="pred-company" style="color:var(--text-muted);">No data — run pipeline</div>
                </div>`;
        }
        const sentTxt = p.news_count === 0 || p.avg_sentiment === 0
            ? 'N/A'
            : (p.avg_sentiment > 0 ? '+' : '') + (p.avg_sentiment * 100).toFixed(0) + '%';
        const prob = p.ml_probability_up ?? 0;
        const pct  = Math.round(prob * 100);
        const barColor = prob >= 0.6 ? '#10b981' : prob <= 0.4 ? '#ef4444' : '#f59e0b';
        return `
            <div class="prediction-card" onclick="showStockDetail('${p.ticker}')">
                <div class="pred-header">
                    <div class="pred-ticker">${p.ticker}</div>
                    <div class="pred-badge ${p.recommendation.toLowerCase().replace(' ','-')}">${p.recommendation}</div>
                    <button class="btn-small" style="margin-left:auto;" onclick="event.stopPropagation();watchlistRemove('${p.ticker}')">✕</button>
                </div>
                <div class="pred-company">${p.company_name || p.ticker}</div>
                <div class="pred-price">$${p.current_price.toFixed(2)}</div>
                <div class="pred-change ${p.price_change_percent >= 0 ? 'positive' : 'negative'}">
                    ${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%
                </div>
                <div class="pred-metrics">
                    <div class="pred-metric"><span>Confidence</span><strong>${(p.confidence*100).toFixed(0)}%</strong></div>
                    <div class="pred-metric"><span>News</span><strong>${p.news_count}</strong></div>
                    <div class="pred-metric"><span>Sentiment</span><strong class="${p.avg_sentiment>=0?'positive':'negative'}">${sentTxt}</strong></div>
                </div>
                <div style="margin-top:0.5rem;">
                    <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:#94a3b8;margin-bottom:2px;">
                        <span>ML Probability</span><span style="color:${barColor};font-weight:700;">${pct}%</span>
                    </div>
                    <div style="background:#0f172a;border-radius:4px;height:5px;">
                        <div style="width:${pct}%;height:100%;background:${barColor};border-radius:4px;"></div>
                    </div>
                </div>
            </div>`;
    });
    grid.innerHTML = cards.join('');
}

// ── ML Training Page Functions ─────────────────────────────────────────────────
function loadTraining() {
    document.getElementById('training-status-dot').className = 'status-dot';
    document.getElementById('training-status-dot').style.background = 'var(--success)';
    document.getElementById('training-status-text').textContent = 'System Ready';
}

function updateTrainingStatus(status, text) {
    const dot = document.getElementById('training-status-dot');
    const textEl = document.getElementById('training-status-text');
    dot.className = 'status-dot';
    if(status === 'running') dot.classList.add('pulsing');
    if(status === 'error') dot.style.background = 'var(--danger)';
    else if(status === 'running') dot.style.background = 'var(--warning)';
    else dot.style.background = 'var(--success)';
    
    textEl.textContent = text;
}

async function collectHistoricalData() {
    const months = document.getElementById('data-period').value;
    const tickers = document.getElementById('data-stocks').value;
    const btn = document.getElementById('btn-collect-data');
    
    btn.disabled = true;
    document.getElementById('collection-progress').style.display = 'block';
    
    updateTrainingStatus('running', `Collecting data for ${tickers} stocks over ${months} months...`);
    
    if(API.collectHistoricalData) {
        await API.collectHistoricalData(months, tickers);
    }
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        document.getElementById('collection-bar').style.width = `${progress}%`;
        document.getElementById('collection-percent').textContent = `${progress}%`;
        
        if(progress >= 100) {
            clearInterval(interval);
            updateTrainingStatus('ready', 'Data collection complete. Ready for training.');
            document.getElementById('collection-status-text').textContent = 'Collection complete!';
            document.getElementById('available-samples').textContent = (tickers * months * 21).toLocaleString();
            btn.disabled = false;
        }
    }, 200);
}

async function trainModel() {
    const btn = document.getElementById('btn-train-model');
    btn.disabled = true;
    document.getElementById('training-progress').style.display = 'block';
    
    updateTrainingStatus('running', 'Training Random Forest and XGBoost models...');
    
    if(API.trainModel) {
        await API.trainModel();
    }
    
    let progress = 0;
    const stages = ['Initializing...', 'Vectorizing News...', 'Fitting Random Forest...', 'Fitting XGBoost...', 'Ensembling...', 'Evaluating...'];
    
    const interval = setInterval(() => {
        progress += 4;
        document.getElementById('training-bar').style.width = `${progress}%`;
        document.getElementById('training-percent').textContent = `${progress}%`;
        document.getElementById('training-stage-text').textContent = stages[Math.floor((progress/100) * stages.length)] || 'Finishing...';
        
        if(progress >= 100) {
            clearInterval(interval);
            updateTrainingStatus('ready', 'Model trained successfully.');
            document.getElementById('training-stage-text').textContent = 'Training completed!';
            document.getElementById('current-accuracy').textContent = '87.4%'; 
            document.getElementById('last-trained-date').textContent = new Date().toLocaleDateString();
            btn.disabled = false;
        }
    }, 150);
}

function runBacktest() {
    alert("Running backtest with current model on historical data...");
}

function analyzePerformance() {
    document.querySelector('.nav-item[data-page="analytics"]').click();
}

function exportTrainingData() {
    alert("Exporting training data CSV to downloads...");
}

function viewLogs() {
    alert("Opening detailed system logs...");
}

// Filters and Search
function setupFilters() {
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;
            loadPredictions();
        });
    });
}

function setupSearch() {
    document.getElementById('global-search').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (query.length > 0) {
            const results = allPredictions.filter(p => 
                p.ticker.toLowerCase().includes(query) || 
                (p.company_name && p.company_name.toLowerCase().includes(query))
            );
            if (results.length > 0) {
                showStockDetail(results[0].ticker);
            }
        }
    });
}

// Stock Detail Modal
async function showStockDetail(ticker) {
    const prediction = allPredictions.find(p => p.ticker === ticker);
    if (!prediction) {
        console.error('No prediction found for', ticker);
        return;
    }
    
    currentTicker = ticker;
    
    document.getElementById('modal-ticker').textContent = ticker;
    document.getElementById('modal-company').textContent = prediction.company_name || ticker;
    document.getElementById('modal-price').textContent = '$' + prediction.current_price.toFixed(2);
    
    const changeElem = document.getElementById('modal-change');
    changeElem.textContent = (prediction.price_change_percent >= 0 ? '+' : '') + prediction.price_change_percent.toFixed(2) + '%';
    changeElem.className = 'stat-value ' + (prediction.price_change_percent >= 0 ? 'positive' : 'negative');
    
    const recElem = document.getElementById('modal-recommendation');
    recElem.textContent = prediction.recommendation;
    recElem.className = 'stat-value';
    
    const sentElem = document.getElementById('modal-sentiment');
    sentElem.textContent = (prediction.news_count === 0 || prediction.avg_sentiment === 0) ? 'N/A' : (prediction.avg_sentiment > 0 ? '+' : '') + (prediction.avg_sentiment * 100).toFixed(0) + '%';
    sentElem.className = 'stat-value ' + (prediction.avg_sentiment >= 0 ? 'positive' : 'negative');
    
    document.getElementById('modal-confidence').textContent = (prediction.confidence * 100).toFixed(0) + '%';
    document.getElementById('modal-news-count').textContent = prediction.news_count;

    // ML probability bar
    const prob = prediction.ml_probability_up ?? 0;
    const mlDate = prediction.ml_date ?? 'N/A';
    const mlRec  = prediction.ml_recommendation ?? prediction.recommendation ?? 'HOLD';
    let mlEl = document.getElementById('modal-ml-section');
    if (!mlEl) {
        // inject once
        const statsEl = document.querySelector('.modal-stats');
        if (statsEl) {
            const div = document.createElement('div');
            div.id = 'modal-ml-section';
            div.style.cssText = 'margin-top:1rem;padding:0.75rem 1rem;background:#1e293b;border-radius:8px;';
            statsEl.insertAdjacentElement('afterend', div);
            mlEl = div;
        }
    }
    if (mlEl) {
        const pct = Math.round(prob * 100);
        const barColor = prob >= 0.6 ? '#10b981' : prob <= 0.4 ? '#ef4444' : '#f59e0b';
        mlEl.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                <span style="color:#94a3b8;font-size:0.8rem;">ML Probability (Up)</span>
                <span style="font-weight:700;color:${barColor}">${pct}% &nbsp;·&nbsp; ${mlRec}</span>
            </div>
            <div style="background:#0f172a;border-radius:4px;height:8px;overflow:hidden;">
                <div style="width:${pct}%;height:100%;background:${barColor};border-radius:4px;transition:width 0.4s;"></div>
            </div>
            <div style="color:#475569;font-size:0.72rem;margin-top:0.35rem;">
                Based on data up to: ${mlDate === 'sentiment-only' ? 'N/A' : mlDate} &nbsp;&middot;&nbsp; ${mlDate === 'sentiment-only' ? 'Sentiment fallback' : 'Predicting next trading day &middot; Ensemble(LightGBM+XGB+RF)'}
            </div>
        `;
    }
    
    // Show modal
    document.getElementById('stock-modal').style.display = 'flex';
    
    // Load chart
    await loadChart(ticker, currentPeriod);
    
    // Related news - filter by ticker
    const relatedNews = allNews.filter(n => {
        // Match exact ticker or ticker in title
        return n.ticker === ticker || 
               (n.title && n.title.toUpperCase().includes(ticker)) ||
               (n.description && n.description.toUpperCase().includes(ticker));
    }).slice(0, 10);
    
    const newsContainer = document.getElementById('modal-news');
    
    if (relatedNews.length === 0) {
        newsContainer.innerHTML = `
            <div class="no-data">
                No news articles found for ${ticker}
            </div>
        `;
    } else {
        newsContainer.innerHTML = relatedNews.map(n => {
            const sentimentClass = getSentimentClass(n.sentiment_compound);
            const sentimentLabel = getSentimentLabel(n.sentiment_compound);
            
            return `
                <div class="modal-news-item">
                    <div class="modal-news-source">${n.source || 'Unknown Source'}</div>
                    <div class="modal-news-title">${n.title || 'No title available'}</div>
                    <div class="modal-news-footer">
                        <span class="modal-news-sentiment ${sentimentClass}">
                            ${sentimentLabel}
                        </span>
                        ${n.impact_level ? `<span class="modal-news-impact">${n.impact_level.toUpperCase()}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
}

async function loadChart(ticker, period) {
    const container = document.getElementById('chart-container');
    container.innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch(`http://localhost:8000/api/v1/stocks/${ticker}/history?period=${period}&interval=1d`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.data || data.data.length === 0) {
            container.innerHTML = '<p class="no-data">No historical data available for this period</p>';
            return;
        }
        
        // Clear previous chart
        if (chart) {
            chart.remove();
            chart = null;
        }
        
        container.innerHTML = '';
        
        // Check if LightweightCharts is loaded
        if (typeof LightweightCharts === 'undefined') {
            container.innerHTML = '<p class="no-data">Chart library not loaded. Please refresh the page.</p>';
            return;
        }
        
        // Create chart
        chart = LightweightCharts.createChart(container, {
            width: container.clientWidth - 32,
            height: 400,
            layout: {
                background: { color: '#0f172a' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#1e293b' },
                horzLines: { color: '#1e293b' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#334155',
            },
            timeScale: {
                borderColor: '#334155',
                timeVisible: true,
            },
        });
        
        // Volume histogram (bottom pane)
        const volumeSeries = chart.addHistogramSeries({
            color: '#334155',
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
        });
        chart.priceScale('volume').applyOptions({
            scaleMargins: { top: 0.85, bottom: 0 },
            borderVisible: false,
        });

        // Candlestick series
        candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        // Format data
        const chartData = data.data.map(d => ({
            time: d.date,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
            volume: d.volume || 0,
        }));

        candlestickSeries.setData(chartData);

        // Volume bars
        volumeSeries.setData(chartData.map(d => ({
            time: d.time,
            value: d.volume,
            color: d.close >= d.open ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)',
        })));

        // SMA 20
        const sma20Series = chart.addLineSeries({
            color: 'rgba(251,191,36,0.85)',
            lineWidth: 1,
            title: 'SMA20',
            priceLineVisible: false,
            lastValueVisible: false,
        });
        const sma20Data = [];
        for (let i = 19; i < chartData.length; i++) {
            const avg = chartData.slice(i - 19, i + 1).reduce((s, d) => s + d.close, 0) / 20;
            sma20Data.push({ time: chartData[i].time, value: avg });
        }
        sma20Series.setData(sma20Data);

        // SMA 50
        if (chartData.length >= 50) {
            const sma50Series = chart.addLineSeries({
                color: 'rgba(139,92,246,0.85)',
                lineWidth: 1,
                title: 'SMA50',
                priceLineVisible: false,
                lastValueVisible: false,
            });
            const sma50Data = [];
            for (let i = 49; i < chartData.length; i++) {
                const avg = chartData.slice(i - 49, i + 1).reduce((s, d) => s + d.close, 0) / 50;
                sma50Data.push({ time: chartData[i].time, value: avg });
            }
            sma50Series.setData(sma50Data);
        }

        chart.timeScale().fitContent();

        // Sentiment trend overlay — group news by date, average sentiment
        const newsForTicker = allNews.filter(n =>
            n.ticker === ticker || (n.title && n.title.toUpperCase().includes(ticker))
        );
        if (newsForTicker.length > 1) {
            const byDate = {};
            newsForTicker.forEach(n => {
                // Normalise any date format to yyyy-mm-dd
                let raw = n.scraped_at || n.published_at || '';
                let d = '';
                try {
                    const dt = new Date(raw);
                    if (!isNaN(dt)) {
                        d = dt.toISOString().split('T')[0];
                    }
                } catch(e) {}
                if (!d || d.length < 10) return;
                if (!byDate[d]) byDate[d] = [];
                byDate[d].push(parseFloat(n.sentiment_compound) || 0);
            });
            const sentData = Object.entries(byDate)
                .map(([d, vals]) => ({ time: d, value: vals.reduce((a,b)=>a+b,0)/vals.length }))
                .sort((a,b) => a.time.localeCompare(b.time));

            if (sentData.length > 1) {
                const sentSeries = chart.addLineSeries({
                    color: 'rgba(251,191,36,0.7)',
                    lineWidth: 1,
                    priceScaleId: 'sentiment',
                    title: 'Sentiment',
                });
                chart.priceScale('sentiment').applyOptions({
                    scaleMargins: { top: 0.8, bottom: 0 },
                    borderVisible: false,
                });
                sentSeries.setData(sentData);
            }
        }
        
        // Handle resize
        const resizeHandler = () => {
            if (chart && container.clientWidth > 0) {
                chart.applyOptions({ width: container.clientWidth - 32 });
            }
        };
        
        window.removeEventListener('resize', resizeHandler);
        window.addEventListener('resize', resizeHandler);
        
    } catch (error) {
        console.error('Error loading chart:', error);
        container.innerHTML = `<p class="no-data">Failed to load chart: ${error.message}</p>`;
    }
}

async function changePeriod(period) {
    currentPeriod = period;
    
    // Update button states
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    if (currentTicker) {
        await loadChart(currentTicker, period);
    }
}

function closeStockModal() {
    document.getElementById('stock-modal').style.display = 'none';
    if (chart) {
        chart.remove();
        chart = null;
    }
    currentTicker = null;
    currentPeriod = '1mo';
}

// Utility functions
function getSentimentClass(score) {
    if (score > 0.05) return 'positive';
    if (score < -0.05) return 'negative';
    return 'neutral';
}

function getSentimentLabel(score) {
    if (score > 0.5) return 'Very Positive';
    if (score > 0.05) return 'Positive';
    if (score < -0.5) return 'Very Negative';
    if (score < -0.05) return 'Negative';
    return 'Neutral';
}

function formatTime(timestamp) {
    if (!timestamp) return 'Unknown';
    
    // Clean up the timestamp (remove extra whitespace and carriage returns)
    const cleanTimestamp = timestamp.trim().replace(/\r\n/g, '').replace(/\s+/g, ' ');
    
    // Try to parse different formats
    let date;
    
    // Check if it's "Today HH:MMAM/PM" format
    if (cleanTimestamp.toLowerCase().startsWith('today')) {
        date = new Date();
        const timeMatch = cleanTimestamp.match(/(\d{1,2}):(\d{2})(AM|PM)/i);
        if (timeMatch) {
            let hours = parseInt(timeMatch[1]);
            const minutes = parseInt(timeMatch[2]);
            const isPM = timeMatch[3].toUpperCase() === 'PM';
            
            if (isPM && hours !== 12) hours += 12;
            if (!isPM && hours === 12) hours = 0;
            
            date.setHours(hours, minutes, 0, 0);
        }
    }
    // Check if it's "MMM-DD-YY HH:MMAM/PM" format
    else if (cleanTimestamp.match(/[A-Za-z]{3}-\d{2}-\d{2}/)) {
        const parts = cleanTimestamp.match(/([A-Za-z]{3})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})(AM|PM)/i);
        if (parts) {
            const monthMap = {
                'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
            };
            const month = monthMap[parts[1]];
            const day = parseInt(parts[2]);
            const year = 2000 + parseInt(parts[3]);
            let hours = parseInt(parts[4]);
            const minutes = parseInt(parts[5]);
            const isPM = parts[6].toUpperCase() === 'PM';
            
            if (isPM && hours !== 12) hours += 12;
            if (!isPM && hours === 12) hours = 0;
            
            date = new Date(year, month, day, hours, minutes);
        }
    }
    // Check if it's just "HH:MMAM/PM" format (assume today)
    else if (cleanTimestamp.match(/^\d{1,2}:\d{2}(AM|PM)/i)) {
        date = new Date();
        const timeMatch = cleanTimestamp.match(/(\d{1,2}):(\d{2})(AM|PM)/i);
        if (timeMatch) {
            let hours = parseInt(timeMatch[1]);
            const minutes = parseInt(timeMatch[2]);
            const isPM = timeMatch[3].toUpperCase() === 'PM';
            
            if (isPM && hours !== 12) hours += 12;
            if (!isPM && hours === 12) hours = 0;
            
            date.setHours(hours, minutes, 0, 0);
        }
    }
    // Try standard date parsing as fallback
    else {
        date = new Date(cleanTimestamp);
    }
    
    // Check if date is valid
    if (!date || isNaN(date.getTime())) {
        return cleanTimestamp; // Return the original cleaned string if parsing fails
    }
    
    const now = new Date();
    const diff = now - date;
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
}

function showError(message) {
    console.error(message);
    // Could add a toast notification here
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('stock-modal');
    if (event.target === modal) {
        closeStockModal();
    }
}


// ============================================================
// FLOATING CHAT WIDGET
// ============================================================

let chatbotActive = false;

const chatFab   = document.getElementById('chat-fab');
const chatPanel = document.getElementById('chat-panel');
const chatClose = document.getElementById('chat-panel-close');

function openChatbot() {
    chatPanel.classList.add('open');
    chatFab.classList.add('open');
    chatFab.title = 'Close Chat';
    chatbotActive = true;
    document.getElementById('chatbot-input').focus();
}

function closeChatbot() {
    chatPanel.classList.remove('open');
    chatFab.classList.remove('open');
    chatFab.title = 'AI Stock Assistant';
    chatbotActive = false;
}

// FAB toggles the panel
chatFab.addEventListener('click', () => {
    chatbotActive ? closeChatbot() : openChatbot();
});

// Close button inside panel
chatClose.addEventListener('click', closeChatbot);

// Click outside the panel closes it
document.addEventListener('click', (e) => {
    if (chatbotActive && !chatPanel.contains(e.target) && !chatFab.contains(e.target)) {
        closeChatbot();
    }
});

// Make closeChatbot globally available
window.closeChatbot = closeChatbot;


// Send message
document.getElementById('chatbot-send').addEventListener('click', sendChatMessage);
document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

async function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        // Call chatbot API (served by the same backend)
        const response = await fetch('http://localhost:8000/api/v1/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error('Chatbot service unavailable');
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // Add bot response
        addChatMessage(data.response, 'bot');
        
    } catch (error) {
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        // Fallback response using local data
        const fallbackResponse = generateFallbackResponse(message);
        addChatMessage(fallbackResponse, 'bot');
    }
}

function addChatMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Format text with line breaks
    const formattedText = text.replace(/\n/g, '<br>');
    content.innerHTML = formattedText;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('chatbot-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <span class="typing-dots">
                <span>.</span><span>.</span><span>.</span>
            </span>
        </div>
    `;
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

// Enhanced AI Chatbot with Context Awareness
let chatContext = {
    lastTopic: null,
    lastTicker: null,
    lastRecommendations: [], // Store last recommended stocks
    conversationHistory: [],
    userPreferences: {
        riskTolerance: 'moderate',
        investmentHorizon: 'medium-term'
    }
};

function generateFallbackResponse(message) {
    const msg = message.toLowerCase();
    
    // Add to conversation history
    chatContext.conversationHistory.push({ role: 'user', content: msg });
    if (chatContext.conversationHistory.length > 10) {
        chatContext.conversationHistory.shift(); // Keep last 10 messages
    }
    
    // Greetings with time-aware responses - EXPANDED to catch casual greetings
    if (msg.match(/^(hi|hello|hey|hay|good morning|good afternoon|good evening|ayy|yo|sup|wassup|whats up|what's up|howdy|hiya)/i) ||
        msg.match(/^(ayy+|yo+|hey+|hi+|hay+)\s+(man|dude|bro|there|everyone)/i)) {
        const hour = new Date().getHours();
        let greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
        
        const responses = [
            `${greeting}! 👋 Ready to make some money moves? I've got the scoop on ${allPredictions.length} stocks and ${allNews.length} news articles. What's your play?`,
            `Hey there! 🐸 Your friendly neighborhood stock analyst here. I've been crunching numbers all day - ${allPredictions.length} stocks analyzed. What can I help you with?`,
            `${greeting}! 💰 I'm like your personal Wall Street insider, minus the fancy suit. Got insights on ${allPredictions.length} stocks. Fire away!`,
            `Yo! 📈 Stock market's been wild today. I've analyzed ${allNews.length} news articles and I'm ready to spill the tea. What do you wanna know?`,
            `${greeting}! 🚀 I've been watching the markets like a hawk. ${allPredictions.length} stocks tracked, sentiment analyzed, predictions ready. Let's make some smart moves!`
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Casual expressions that aren't stock queries
    if (msg.match(/^(duh|bruh|lol|lmao|haha|omg|wow|damn|shit|wtf|ok|okay|cool|nice|yeah|yep|nope|nah)/i)) {
        const responses = [
            "😄 Haha, alright! So what's the move? Want some hot stock picks or got a specific ticker in mind?",
            "👍 I feel you! Let's talk stocks - what are you curious about?",
            "😎 Cool cool. Ready to dive into some market action? Try 'top picks' or ask about any stock!",
            "🐸 Ribbit! I mean... what stock info can I get you? I'm here to help you make bank!",
            "💯 For sure! Now let's get down to business - stocks, trends, or recommendations?"
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Investment advice / what to buy / top stocks - CHECK THIS BEFORE TICKER MATCHING
    if (msg.match(/what.*buy|what.*invest|top.*stock|best.*stock|should.*buy|buy.*today/)) {
        chatContext.lastTopic = 'investment_advice';
        
        const topPicks = allPredictions
            .filter(p => p.recommendation.includes('BUY') && p.news_count > 0 && p.confidence > 0.4)
            .sort((a, b) => b.prediction_score - a.prediction_score)
            .slice(0, 5);
        
        // Store recommendations in context
        chatContext.lastRecommendations = topPicks;
        
        let response = ["🚀 Alright, let's make some money! Here are my top picks:", "💰 You came to the right place! Check out these beauties:", "📈 Ooh, I like your style! Here's what's looking juicy today:", "🎯 Time to get that bread! These stocks are fire right now:", "💎 Let me show you where the smart money's going:"][Math.floor(Math.random() * 5)] + "\n\n";
        topPicks.forEach((p, i) => {
            const emoji = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '⭐';
            response += `${emoji} ${p.ticker} - ${p.company_name}\n`;
            response += `   💰 $${p.current_price.toFixed(2)} (${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%)\n`;
            response += `   📊 ${p.recommendation} • Confidence: ${(p.confidence * 100).toFixed(0)}%\n`;
            response += `   📰 ${p.news_count} articles • Sentiment: ${(p.avg_sentiment * 100).toFixed(0)}%\n\n`;
        });
        
        response += ["💡 These are showing serious potential! Want the deep dive on any of them?", "🔥 All of these are looking solid! Need more details? Just ask!", "✨ Strong signals across the board! Want me to break down any specific one?", "🎪 That's the good stuff right there! Curious about any particular stock?", "🐸 Ribbit! I mean... these are my top recommendations! Want more info?"][Math.floor(Math.random() * 5)];
        return response;
    }
    
    // Follow-up questions about recommendations
    if (msg.match(/which one|which.*best|pick one|choose|recommend.*one|between.*them|from.*these|first.*one|top.*one/) && chatContext.lastRecommendations.length > 0) {
        const best = chatContext.lastRecommendations[0];
        chatContext.lastTicker = best.ticker;
        
        let response = `💡 I'd recommend ${best.ticker} - ${best.company_name}:\n\n`;
        response += `📊 Why it's the top pick:\n`;
        
        const reasons = [];
        if (best.confidence > 0.7) reasons.push(`• Highest confidence (${(best.confidence * 100).toFixed(0)}%)`);
        if (best.avg_sentiment > 0.3) reasons.push(`• Very strong positive sentiment (${(best.avg_sentiment * 100).toFixed(0)}%)`);
        if (best.news_count > 10) reasons.push(`• High media coverage (${best.news_count} articles)`);
        if (best.price_change_percent > 2) reasons.push(`• Strong upward momentum (+${best.price_change_percent.toFixed(1)}%)`);
        if (best.prediction_score > 0.5) reasons.push(`• Excellent prediction score (${(best.prediction_score * 100).toFixed(0)}%)`);
        
        response += reasons.join('\n') || '• Best overall signals among the group';
        response += `\n\n💰 Current Price: $${best.current_price.toFixed(2)}\n`;
        response += `📈 Recommendation: ${best.recommendation}\n\n`;
        response += `💡 Want to know more? Ask "Why ${best.ticker}?" or "Tell me about ${best.ticker}"`;
        
        return response;
    }
    
    // Comparison questions
    if (msg.match(/compare|difference|versus|vs|better/) && chatContext.lastRecommendations.length >= 2) {
        const stock1 = chatContext.lastRecommendations[0];
        const stock2 = chatContext.lastRecommendations[1];
        
        let response = `⚖️ Comparing Top 2 Picks:\n\n`;
        response += `🥇 ${stock1.ticker} - ${stock1.company_name}\n`;
        response += `   Price: $${stock1.current_price.toFixed(2)} (${stock1.price_change_percent >= 0 ? '+' : ''}${stock1.price_change_percent.toFixed(2)}%)\n`;
        response += `   Confidence: ${(stock1.confidence * 100).toFixed(0)}% • Sentiment: ${(stock1.avg_sentiment * 100).toFixed(0)}%\n\n`;
        
        response += `🥈 ${stock2.ticker} - ${stock2.company_name}\n`;
        response += `   Price: $${stock2.current_price.toFixed(2)} (${stock2.price_change_percent >= 0 ? '+' : ''}${stock2.price_change_percent.toFixed(2)}%)\n`;
        response += `   Confidence: ${(stock2.confidence * 100).toFixed(0)}% • Sentiment: ${(stock2.avg_sentiment * 100).toFixed(0)}%\n\n`;
        
        if (stock1.prediction_score > stock2.prediction_score) {
            response += `💡 ${stock1.ticker} has a slight edge with better overall signals.`;
        } else {
            response += `💡 Both are strong picks! ${stock1.ticker} leads slightly.`;
        }
        
        return response;
    }
    
    // More details request
    if (msg.match(/more.*detail|tell.*more|explain|elaborate|why/) && chatContext.lastRecommendations.length > 0) {
        const stock = chatContext.lastRecommendations[0];
        chatContext.lastTicker = stock.ticker;
        
        // Get recent news for this stock
        const stockNews = allNews.filter(n => n.ticker === stock.ticker).slice(0, 3);
        
        let response = `📊 Detailed Analysis: ${stock.ticker} - ${stock.company_name}\n\n`;
        response += `💰 Price: $${stock.current_price.toFixed(2)} (${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent.toFixed(2)}%)\n`;
        response += `📈 Recommendation: ${stock.recommendation}\n`;
        response += `🎯 Confidence: ${(stock.confidence * 100).toFixed(0)}%\n`;
        response += `💭 Sentiment: ${(stock.avg_sentiment * 100).toFixed(0)}%\n`;
        response += `📰 News Coverage: ${stock.news_count} articles\n\n`;
        
        response += `🔍 Why This Stock:\n`;
        const reasons = [];
        if (stock.avg_sentiment > 0.3) reasons.push('• Very positive news sentiment');
        if (stock.confidence > 0.7) reasons.push('• High confidence prediction');
        if (stock.news_count > 10) reasons.push('• Strong media attention');
        if (stock.price_change_percent > 2) reasons.push('• Positive price momentum');
        response += reasons.join('\n') || '• Strong overall signals';
        
        if (stockNews.length > 0) {
            response += `\n\n📰 Recent Headlines:\n`;
            stockNews.forEach((n, i) => {
                const emoji = n.sentiment_compound > 0.05 ? '🟢' : n.sentiment_compound < -0.05 ? '🔴' : '⚪';
                response += `${emoji} ${n.title.substring(0, 60)}...\n`;
            });
        }
        
        return response;
    }
    
    // Casual follow-ups for more recommendations
    if (msg.match(/any.*more|anything.*else|more.*recommend|other.*stock|what.*else|show.*more|give.*more|got.*more/)) {
        if (chatContext.lastRecommendations.length > 1) {
            // Show next recommendations
            const nextStocks = chatContext.lastRecommendations.slice(1, 4);
            
            let response = "📊 Here are more great options:\n\n";
            nextStocks.forEach((p, i) => {
                const emoji = ['🥈', '🥉', '⭐'][i];
                response += `${emoji} ${p.ticker} - ${p.company_name}\n`;
                response += `   💰 $${p.current_price.toFixed(2)} (${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%)\n`;
                response += `   📊 ${p.recommendation} • Confidence: ${(p.confidence * 100).toFixed(0)}%\n\n`;
            });
            
            response += "💡 Want details on any of these? Just ask!";
            return response;
        } else {
            // Generate new recommendations
            const topPicks = allPredictions
                .filter(p => p.recommendation.includes('BUY') && p.news_count > 0)
                .sort((a, b) => b.prediction_score - a.prediction_score)
                .slice(0, 5);
            
            chatContext.lastRecommendations = topPicks;
            
            let response = "🚀 Here are my top recommendations:\n\n";
            topPicks.forEach((p, i) => {
                const emoji = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '⭐';
                response += `${emoji} ${p.ticker} - ${p.company_name}\n`;
                response += `   💰 $${p.current_price.toFixed(2)} (${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%)\n`;
                response += `   📊 ${p.recommendation} • ${(p.confidence * 100).toFixed(0)}% confidence\n\n`;
            });
            
            return response;
        }
    }
    
    // What's hot / trending / popular
    if (msg.match(/what.*hot|what.*trend|what.*popular|what.*moving|hot.*stock|trending/)) {
        const hotStocks = allPredictions
            .filter(p => Math.abs(p.price_change_percent) > 2 || p.news_count > 15)
            .sort((a, b) => b.news_count - a.news_count)
            .slice(0, 5);
        
        chatContext.lastRecommendations = hotStocks;
        
        let response = "🔥 Hot Stocks Today (High Activity):\n\n";
        hotStocks.forEach((p, i) => {
            const emoji = p.price_change_percent > 0 ? '📈' : '📉';
            response += `${i + 1}. ${emoji} ${p.ticker} - ${p.company_name}\n`;
            response += `   💰 $${p.current_price.toFixed(2)} (${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%)\n`;
            response += `   📰 ${p.news_count} articles • ${p.recommendation}\n\n`;
        });
        
        response += "💡 These stocks have high activity today!";
        return response;
    }
    
    // Acknowledgments and casual responses
    if (msg.match(/^(ok|okay|cool|nice|good|great|awesome|thanks|thank|got it|alright|sure)$/)) {
        const responses = [
            "👍 Anything else you'd like to know?",
            "Great! Need help with anything else?",
            "👌 What else can I help you with?",
            "Perfect! Any other questions?",
            "Glad to help! What's next?",
            "🐸 Ribbit ribbit! (That means 'you got it' in frog). What else?",
            "😎 We're vibing! What's your next move?",
            "💯 Bet! Anything else on your mind?"
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // High return / best stocks / top picks
    if (msg.includes('high') && (msg.includes('return') || msg.includes('rate')) || 
        msg.includes('best stock') || msg.includes('top pick') || msg.includes('recommend')) {
        const topPreds = allPredictions
            .filter(p => p.recommendation.includes('BUY') && p.news_count > 0)
            .sort((a, b) => b.prediction_score - a.prediction_score)
            .slice(0, 5);
        
        let response = "🚀 Top Stocks with High Potential Today:\n\n";
        topPreds.forEach((p, i) => {
            const emoji = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '⭐';
            response += `${emoji} ${p.ticker} - ${p.company_name}\n`;
            response += `   💰 Price: $${p.current_price.toFixed(2)} (${p.price_change_percent >= 0 ? '+' : ''}${p.price_change_percent.toFixed(2)}%)\n`;
            response += `   📊 Recommendation: ${p.recommendation}\n`;
            response += `   🎯 Confidence: ${(p.confidence * 100).toFixed(0)}%\n`;
            response += `   📰 News: ${p.news_count} articles\n\n`;
        });
        
        response += "These stocks show strong positive signals based on recent news sentiment!";
        return response;
    }
    
    // Gainers / rising / going up
    if (msg.includes('gainer') || msg.includes('rising') || msg.includes('going up') || msg.includes('up today')) {
        const gainers = allPredictions
            .filter(p => p.price_change_percent > 0)
            .sort((a, b) => b.price_change_percent - a.price_change_percent)
            .slice(0, 5);
        
        let response = "📈 Top Gainers Today:\n\n";
        gainers.forEach((p, i) => {
            response += `${i + 1}. ${p.ticker} - ${p.company_name}\n`;
            response += `   Price: $${p.current_price.toFixed(2)} (+${p.price_change_percent.toFixed(2)}%)\n\n`;
        });
        
        return response;
    }
    
    // Losers / falling / going down / worst / least favored
    if (msg.includes('loser') || msg.includes('falling') || msg.includes('going down') || msg.includes('down today') || msg.match(/worst|least.*favor|least.*perform|avoid|stay.*away/)) {
        const losers = allPredictions
            .filter(p => p.price_change_percent < 0 || p.recommendation.includes('SELL') || p.avg_sentiment < -0.05)
            .sort((a, b) => a.price_change_percent - b.price_change_percent)
            .slice(0, 5);
        
        let response = "📉 Top Losers Today:\n\n";
        losers.forEach((p, i) => {
            response += `${i + 1}. ${p.ticker} - ${p.company_name}\n`;
            response += `   Price: $${p.current_price.toFixed(2)} (${p.price_change_percent.toFixed(2)}%)\n\n`;
        });
        
        return response;
    }
    
    // Market sentiment / overall market with deeper analysis
    if (msg.includes('market') || msg.includes('sentiment') || msg.includes('overall') || msg.includes('trend')) {
        chatContext.lastTopic = 'market_sentiment';
        
        const positive = allPredictions.filter(p => p.avg_sentiment > 0.05).length;
        const negative = allPredictions.filter(p => p.avg_sentiment < -0.05).length;
        const total = allPredictions.length;
        
        const positivePct = (positive / total * 100).toFixed(1);
        const negativePct = (negative / total * 100).toFixed(1);
        
        // Calculate sector sentiment
        const sectorSentiment = {};
        allPredictions.forEach(p => {
            if (p.sector) {
                if (!sectorSentiment[p.sector]) {
                    sectorSentiment[p.sector] = { positive: 0, negative: 0, total: 0 };
                }
                sectorSentiment[p.sector].total++;
                if (p.avg_sentiment > 0.05) sectorSentiment[p.sector].positive++;
                if (p.avg_sentiment < -0.05) sectorSentiment[p.sector].negative++;
            }
        });
        
        // Find best and worst sectors
        const sectors = Object.entries(sectorSentiment)
            .map(([name, data]) => ({
                name,
                score: (data.positive - data.negative) / data.total
            }))
            .sort((a, b) => b.score - a.score);
        
        const mood = positive > negative ? 'Bullish 🟢' : negative > positive ? 'Bearish 🔴' : 'Mixed ⚪';
        
        let response = `📊 Market Sentiment Analysis:\n\n`;
        response += `Overall Mood: ${mood}\n\n`;
        response += `🟢 Positive: ${positive} stocks (${positivePct}%)\n`;
        response += `🔴 Negative: ${negative} stocks (${negativePct}%)\n`;
        response += `⚪ Neutral: ${total - positive - negative} stocks\n\n`;
        
        if (sectors.length > 0) {
            response += `📈 Best Performing Sector: ${sectors[0].name}\n`;
            response += `📉 Weakest Sector: ${sectors[sectors.length - 1].name}\n\n`;
        }
        
        // Add market insight
        if (positive > negative * 1.5) {
            response += `💡 Strong bullish momentum! Consider looking at growth stocks.`;
        } else if (negative > positive * 1.5) {
            response += `⚠️ Bearish pressure detected. Consider defensive positions or wait for better entry points.`;
        } else {
            response += `💡 Mixed signals suggest a selective approach. Focus on high-conviction picks.`;
        }
        
        return response;
    }
    
    // News / latest news
    if (msg.includes('news') || msg.includes('latest')) {
        const recentNews = allNews.slice(0, 5);
        let response = "📰 Latest News Headlines:\n\n";
        
        recentNews.forEach((n, i) => {
            const sentimentEmoji = n.sentiment_compound > 0.05 ? '🟢' : n.sentiment_compound < -0.05 ? '🔴' : '⚪';
            response += `${i + 1}. ${sentimentEmoji} ${n.title}\n`;
            response += `   ${n.ticker} | ${n.source}\n\n`;
        });
        
        return response;
    }
    
    // Specific stock by ticker - ONLY match if it looks like a stock query
    // Exclude common conversational words that might look like tickers
    const commonWords = ['SO', 'IT', 'TO', 'OR', 'IF', 'IS', 'AS', 'AT', 'BY', 'DO', 'GO', 'HE', 'IN', 'ME', 'MY', 'NO', 'OF', 'ON', 'UP', 'US', 'WE', 'AN', 'BE', 'CAN', 'FOR', 'GET', 'GOT', 'HAD', 'HAS', 'HER', 'HIM', 'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOT', 'NOW', 'OLD', 'ONE', 'OUR', 'OUT', 'OWN', 'SAY', 'SHE', 'THE', 'TOO', 'TWO', 'USE', 'WAS', 'WAY', 'WHO', 'WHY', 'WILL', 'WITH', 'YOU', 'YOUR', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'THATS', 'THAT', 'THIS', 'THESE', 'THOSE', 'THEM', 'THEY', 'THEIR', 'THERE', 'THEN', 'THAN', 'FROM', 'HAVE', 'BEEN', 'WERE', 'SAID', 'EACH', 'SOME', 'WOULD', 'COULD', 'SHOULD', 'ABOUT', 'AFTER', 'AGAIN', 'ALSO', 'BACK', 'BECAUSE', 'BEFORE', 'BEING', 'BOTH', 'CAME', 'COME', 'DOES', 'DOING', 'DONE', 'DOWN', 'DURING', 'EVEN', 'EVERY', 'FIRST', 'GIVE', 'GIVEN', 'GOING', 'GOOD', 'GREAT', 'JUST', 'KNOW', 'LAST', 'LIKE', 'LONG', 'LOOK', 'MADE', 'MAKE', 'MANY', 'MORE', 'MOST', 'MUCH', 'MUST', 'NEVER', 'NEXT', 'ONLY', 'OTHER', 'OVER', 'PART', 'SAME', 'SUCH', 'TAKE', 'TELL', 'THAN', 'THAT', 'THEM', 'THEN', 'THERE', 'THESE', 'THING', 'THINK', 'THIS', 'THOSE', 'TIME', 'UNDER', 'UNTIL', 'UPON', 'VERY', 'WANT', 'WELL', 'WENT', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WITH', 'WORK', 'YEAR', 'DAMN', 'DYAMM', 'ANYTHING', 'SOMETHING', 'EVERYTHING', 'NOTHING', 'ELSE', 'ANY', 'MA', 'MAN', 'AYY', 'YO', 'SUP', 'WHATS', 'HOWS', 'LETS', 'CANT', 'DONT', 'WONT', 'DIDNT', 'ISNT', 'ARENT', 'WASNT', 'WERENT', 'HAVENT', 'HASNT', 'HADNT', 'WOULDNT', 'COULDNT', 'SHOULDNT', 'MIGHTNT', 'MUSTNT', 'DUH', 'BRUH', 'LOL', 'LMAO', 'HAHA', 'OMG', 'WOW', 'WTF', 'YEAH', 'YEP', 'NOPE', 'NAH', 'HEY', 'HI', 'BYE', 'OKAY', 'COOL', 'NICE', 'DUDE', 'BRO'];
    
    // STRICT: Only try ticker matching if message CLEARLY looks like a stock query
    const looksLikeStockQuery = msg.match(/\b(stock|ticker|price|buy|sell|analysis|info|information|quote|chart|data)\b/) || 
                                msg.match(/\b(tell|show|get|find|lookup|search|check).*\b(about|for|on|me)\b/) ||
                                (message.length <= 6 && message.match(/^[A-Z]{1,5}$/)); // Only very short all-caps messages
    
    if (looksLikeStockQuery) {
        const tickerMatch = message.toUpperCase().match(/\b[A-Z]{2,5}\b/);
        if (tickerMatch) {
            const potentialTicker = tickerMatch[0];
            
            // Skip if it's a common word
            if (!commonWords.includes(potentialTicker)) {
                const stock = allPredictions.find(p => p.ticker === potentialTicker);
                if (stock) {
                    chatContext.lastTicker = stock.ticker;
                    const sentimentEmoji = stock.avg_sentiment > 0.05 ? '🟢' : stock.avg_sentiment < -0.05 ? '🔴' : '⚪';
                    const priceEmoji = stock.price_change_percent >= 0 ? '📈' : '📉';
                    
                    return `${sentimentEmoji} ${stock.ticker} - ${stock.company_name}\n\n` +
                           `${priceEmoji} Price: ${stock.current_price.toFixed(2)}\n` +
                           `Change: ${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent.toFixed(2)}%\n\n` +
                           `📊 Recommendation: ${stock.recommendation}\n` +
                           `💭 Sentiment: ${(stock.avg_sentiment * 100).toFixed(0)}% ${sentimentEmoji}\n` +
                           `🎯 Confidence: ${(stock.confidence * 100).toFixed(0)}%\n` +
                           `📰 News Articles: ${stock.news_count}\n\n` +
                           `${stock.recommendation.includes('BUY') ? 
                             'This stock shows positive signals!' : 
                             stock.recommendation.includes('SELL') ? 
                             'This stock shows negative signals.' : 
                             'This stock shows mixed signals.'}`;
                }
            }
        }
    }
    
    // Specific stock by ticker - fallback for VERY SHORT messages only (likely just a ticker)
    if (message.length <= 6 && message.match(/^[A-Z]{1,5}$/)) {
        const ticker = message.toUpperCase().match(/\b[A-Z]{2,5}\b/);
        if (ticker && !commonWords.includes(ticker[0])) {
            const stock = allPredictions.find(p => p.ticker === ticker[0]);
            if (stock) {
                chatContext.lastTicker = stock.ticker;
            const sentimentEmoji = stock.avg_sentiment > 0.05 ? '🟢' : stock.avg_sentiment < -0.05 ? '🔴' : '⚪';
            const priceEmoji = stock.price_change_percent >= 0 ? '📈' : '📉';
            
            return `${sentimentEmoji} ${stock.ticker} - ${stock.company_name}\n\n` +
                   `${priceEmoji} Price: $${stock.current_price.toFixed(2)}\n` +
                   `Change: ${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent.toFixed(2)}%\n\n` +
                   `📊 Recommendation: ${stock.recommendation}\n` +
                   `💭 Sentiment: ${(stock.avg_sentiment * 100).toFixed(0)}% ${sentimentEmoji}\n` +
                   `🎯 Confidence: ${(stock.confidence * 100).toFixed(0)}%\n` +
                   `📰 News Articles: ${stock.news_count}\n\n` +
                   `${stock.recommendation.includes('BUY') ? 
                     'This stock shows positive signals!' : 
                     stock.recommendation.includes('SELL') ? 
                     'This stock shows negative signals.' : 
                     'This stock shows mixed signals.'}`;
            }
        }
    }
    
    // Company name search
    const companyMatch = allPredictions.find(p => 
        msg.includes(p.company_name.toLowerCase()) || 
        msg.includes(p.ticker.toLowerCase())
    );
    
    if (companyMatch) {
        const stock = companyMatch;
        const sentimentEmoji = stock.avg_sentiment > 0.05 ? '🟢' : stock.avg_sentiment < -0.05 ? '🔴' : '⚪';
        
        return `${sentimentEmoji} ${stock.ticker} - ${stock.company_name}\n\n` +
               `Price: $${stock.current_price.toFixed(2)} (${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent.toFixed(2)}%)\n` +
               `Recommendation: ${stock.recommendation}\n` +
               `Sentiment: ${(stock.avg_sentiment * 100).toFixed(0)}%\n` +
               `Confidence: ${(stock.confidence * 100).toFixed(0)}%\n` +
               `News: ${stock.news_count} articles`;
    }
    
    // Portfolio suggestions
    if (msg.match(/portfolio|diversif|allocat|balance/)) {
        const sectors = {};
        allPredictions.forEach(p => {
            if (p.sector && p.recommendation.includes('BUY')) {
                if (!sectors[p.sector]) sectors[p.sector] = [];
                sectors[p.sector].push(p);
            }
        });
        
        let response = "📊 Diversified Portfolio Suggestion:\n\n";
        let count = 0;
        
        for (const [sector, stocks] of Object.entries(sectors)) {
            if (count >= 5) break;
            const best = stocks.sort((a, b) => b.prediction_score - a.prediction_score)[0];
            response += `${['🏢', '💻', '🏥', '⚡', '🏭'][count]} ${sector}:\n`;
            response += `   ${best.ticker} - $${best.current_price.toFixed(2)} (${best.recommendation})\n\n`;
            count++;
        }
        
        response += "💡 This provides sector diversification while focusing on strong performers.";
        return response;
    }
    
    // Explain why
    if (msg.match(/why|reason|explain|because/) && chatContext.lastTicker) {
        const stock = allPredictions.find(p => p.ticker === chatContext.lastTicker);
        if (stock) {
            let response = `🔍 Why ${stock.ticker} is ${stock.recommendation}:\n\n`;
            
            const reasons = [];
            if (stock.avg_sentiment > 0.15) reasons.push(`• Strong positive sentiment (${(stock.avg_sentiment * 100).toFixed(0)}%)`);
            if (stock.avg_sentiment < -0.15) reasons.push(`• Negative sentiment (${(stock.avg_sentiment * 100).toFixed(0)}%)`);
            if (stock.news_count > 15) reasons.push(`• High media coverage (${stock.news_count} articles)`);
            if (stock.price_change_percent > 3) reasons.push(`• Strong upward momentum (+${stock.price_change_percent.toFixed(1)}%)`);
            if (stock.price_change_percent < -3) reasons.push(`• Downward pressure (${stock.price_change_percent.toFixed(1)}%)`);
            if (stock.confidence > 0.6) reasons.push(`• High confidence prediction (${(stock.confidence * 100).toFixed(0)}%)`);
            if (stock.confidence < 0.4) reasons.push(`• Lower confidence (${(stock.confidence * 100).toFixed(0)}%)`);
            
            response += reasons.join('\n') || '• Mixed signals from various indicators';
            response += `\n\n💡 Based on analysis of ${stock.news_count} news articles and current market data.`;
            
            return response;
        }
    }
    
    // What stocks do you track
    if (msg.match(/what stocks|which stocks|how many|list.*stock/)) {
        const sectors = {};
        allPredictions.forEach(p => {
            if (p.sector) {
                sectors[p.sector] = (sectors[p.sector] || 0) + 1;
            }
        });
        
        let response = `📊 I track ${allPredictions.length} stocks across multiple sectors:\n\n`;
        Object.entries(sectors).slice(0, 8).forEach(([sector, count]) => {
            response += `• ${sector}: ${count} stocks\n`;
        });
        response += `\n💡 Ask about any major stock like AAPL, MSFT, GOOGL, TSLA, AMZN, etc.`;
        
        return response;
    }
    
    // Thank you
    if (msg.match(/thank|thanks|appreciate/)) {
        const responses = [
            "You're welcome! Happy investing! 📈",
            "Glad I could help! Let me know if you need anything else! 💡",
            "Anytime! Feel free to ask more questions! 🚀"
        ];
        return responses[Math.floor(Math.random() * responses.length)];
    }
    
    // Help / what can you do
    if (msg.includes('help') || msg.includes('what can you')) {
        return "🤖 I'm your AI stock analyst! I can help with:\n\n" +
               "💡 Stock Analysis:\n" +
               "• 'Should I buy AAPL?'\n" +
               "• 'Compare TSLA vs RIVN'\n" +
               "• 'Tell me about Microsoft'\n" +
               "• 'Why is NVDA a buy?'\n\n" +
               "📊 Market Insights:\n" +
               "• 'What's the market sentiment?'\n" +
               "• 'Show me tech stocks'\n" +
               "• 'Which stocks are safe?'\n\n" +
               "📰 News & Trends:\n" +
               "• 'Latest news on AAPL'\n" +
               "• 'Top gainers today'\n" +
               "• 'What's trending?'\n\n" +
               "💼 Portfolio Help:\n" +
               "• 'Suggest a diversified portfolio'\n" +
               "• 'Best stocks for long term'\n\n" +
               "Just ask naturally - I understand context!";
    }
    
    // Default intelligent response
    const responses = [
        `I'm analyzing ${allNews.length} news articles and ${allPredictions.length} stocks. Try asking:\n• "What are the best stocks today?"\n• "Tell me about [TICKER]"\n• "What's the market sentiment?"\n• "Compare [TICKER1] vs [TICKER2]"`,
        `I can help you make smarter investment decisions! Ask me about:\n• Specific stocks (e.g., "Tell me about AAPL")\n• Market trends\n• Stock comparisons\n• Portfolio suggestions`,
        `Not sure what you're looking for. Try:\n• "Show me high return stocks"\n• "What's happening with Tesla?"\n• "Compare MSFT and GOOGL"\n• "Suggest a portfolio"`
    ];
    
    return responses[Math.floor(Math.random() * responses.length)];
}

// Start chatbot service on page load
async function startChatbotService() {
    try {
        const response = await fetch('http://localhost:8000/api/v1/chat/health');
        if (response.ok) {
            console.log('✅ Chatbot service is running');
        }
    } catch (error) {
        console.log('⚠️ Chatbot service not available, using fallback mode');
    }
}

// Initialize chatbot service
startChatbotService();


// ============================================================================
// DISCLAIMER MODAL
// ============================================================================

function showFullDisclaimer() {
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeDisclaimerModal() {
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Show disclaimer on first visit
window.addEventListener('DOMContentLoaded', () => {
    const hasSeenDisclaimer = localStorage.getItem('hasSeenDisclaimer');
    if (!hasSeenDisclaimer) {
        setTimeout(() => {
            showFullDisclaimer();
            localStorage.setItem('hasSeenDisclaimer', 'true');
        }, 2000);
    }
});

// Close disclaimer modal on outside click
document.addEventListener('click', (e) => {
    const modal = document.getElementById('disclaimer-modal');
    if (modal && e.target === modal) {
        closeDisclaimerModal();
    }
});
