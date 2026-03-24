// Stock Predictor Frontend App

const API_URL = 'http://localhost:8000/api';

let recommendationChart = null;
let sentimentChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadPredictions();
    loadNews();
    loadStocks();
});

// Show section
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(`${section}-section`).classList.add('active');
    
    // Update sidebar
    document.querySelectorAll('.sidebar-menu li').forEach(el => {
        el.classList.remove('active');
    });
    event.target.closest('li').classList.add('active');
}

// Load Dashboard
async function loadDashboard() {
    try {
        // Load stats
        const stats = await fetch(`${API_URL}/stats`).then(r => r.json());
        
        document.getElementById('totalStocks').textContent = stats.total_stocks;
        document.getElementById('buySignals').textContent = stats.buy_signals;
        document.getElementById('sellSignals').textContent = stats.sell_signals;
        document.getElementById('totalNews').textContent = stats.total_news;
        
        if (stats.last_updated) {
            const date = new Date(stats.last_updated);
            document.getElementById('lastUpdated').textContent = 
                `Updated: ${date.toLocaleTimeString()}`;
        }
        
        // Load predictions for charts
        const predictions = await fetch(`${API_URL}/predictions`).then(r => r.json());
        
        // Recommendation Chart
        createRecommendationChart(stats);
        
        // Sentiment Chart
        createSentimentChart(predictions);
        
        // Top Predictions Table
        createTopPredictionsTable(predictions);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Create Recommendation Chart
function createRecommendationChart(stats) {
    const ctx = document.getElementById('recommendationChart');
    
    if (recommendationChart) {
        recommendationChart.destroy();
    }
    
    recommendationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['BUY', 'SELL', 'HOLD'],
            datasets: [{
                data: [stats.buy_signals, stats.sell_signals, stats.hold_signals],
                backgroundColor: ['#1cc88a', '#e74a3b', '#f6c23e'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Create Sentiment Chart
function createSentimentChart(predictions) {
    const ctx = document.getElementById('sentimentChart');
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    const labels = predictions.map(p => p.ticker);
    const sentiments = predictions.map(p => p.sentiment_score);
    const colors = sentiments.map(s => s > 0 ? '#1cc88a' : s < 0 ? '#e74a3b' : '#f6c23e');
    
    sentimentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment Score',
                data: sentiments,
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    min: -1,
                    max: 1
                }
            }
        }
    });
}

// Create Top Predictions Table
function createTopPredictionsTable(predictions) {
    // Sort by confidence
    predictions.sort((a, b) => b.confidence - a.confidence);
    
    const top5 = predictions.slice(0, 5);
    
    let html = `
        <table class="table">
            <thead>
                <tr>
                    <th>Stock</th>
                    <th>Price</th>
                    <th>Change</th>
                    <th>Sentiment</th>
                    <th>Confidence</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    top5.forEach(pred => {
        const changeClass = pred.predicted_change_pct > 0 ? 'text-success' : 'text-danger';
        const changeIcon = pred.predicted_change_pct > 0 ? '↑' : '↓';
        
        html += `
            <tr>
                <td>
                    <strong>${pred.ticker}</strong><br>
                    <small class="text-muted">${pred.company}</small>
                </td>
                <td>$${pred.current_price.toFixed(2)}</td>
                <td class="${changeClass}">
                    ${changeIcon} ${Math.abs(pred.predicted_change_pct).toFixed(2)}%
                </td>
                <td>
                    <span class="badge ${getSentimentClass(pred.sentiment)}">
                        ${pred.sentiment}
                    </span>
                </td>
                <td>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                    </div>
                    <small>${(pred.confidence * 100).toFixed(0)}%</small>
                </td>
                <td>
                    <span class="badge badge-${pred.recommendation.toLowerCase()}">
                        ${pred.recommendation}
                    </span>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    
    document.getElementById('topPredictions').innerHTML = html;
}

// Load Predictions
async function loadPredictions() {
    try {
        const predictions = await fetch(`${API_URL}/predictions`).then(r => r.json());
        
        let html = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Stock</th>
                        <th>Current Price</th>
                        <th>Predicted Price</th>
                        <th>Change</th>
                        <th>Sentiment</th>
                        <th>News</th>
                        <th>Confidence</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        predictions.forEach(pred => {
            const changeClass = pred.predicted_change_pct > 0 ? 'text-success' : 'text-danger';
            const changeIcon = pred.predicted_change_pct > 0 ? '↑' : '↓';
            
            html += `
                <tr>
                    <td>
                        <strong>${pred.ticker}</strong><br>
                        <small class="text-muted">${pred.company}</small>
                    </td>
                    <td>$${pred.current_price.toFixed(2)}</td>
                    <td>$${pred.predicted_price.toFixed(2)}</td>
                    <td class="${changeClass}">
                        ${changeIcon} ${Math.abs(pred.predicted_change_pct).toFixed(2)}%
                    </td>
                    <td>
                        <span class="badge ${getSentimentClass(pred.sentiment)}">
                            ${pred.sentiment}
                        </span>
                        <br>
                        <small>${pred.sentiment_score.toFixed(3)}</small>
                    </td>
                    <td>${pred.news_count} articles</td>
                    <td>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${pred.confidence * 100}%"></div>
                        </div>
                        ${(pred.confidence * 100).toFixed(0)}%
                    </td>
                    <td>
                        <span class="badge badge-${pred.recommendation.toLowerCase()}">
                            ${pred.recommendation}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        
        document.getElementById('predictionsTable').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading predictions:', error);
        document.getElementById('predictionsTable').innerHTML = 
            '<p class="text-danger">Error loading predictions</p>';
    }
}

// Load News
async function loadNews() {
    try {
        const news = await fetch(`${API_URL}/news?limit=20`).then(r => r.json());
        
        let html = '';
        
        news.forEach(article => {
            const sentimentBadge = article.sentiment_score !== null ? 
                `<span class="sentiment-badge ${getSentimentClassFromScore(article.sentiment_score)}">
                    ${article.sentiment_score > 0 ? 'Positive' : article.sentiment_score < 0 ? 'Negative' : 'Neutral'}
                </span>` : '';
            
            html += `
                <div class="news-item">
                    <h6>${article.title}</h6>
                    <div class="news-meta">
                        <span><i class="fas fa-building"></i> ${article.source}</span>
                        <span class="ms-3"><i class="fas fa-chart-line"></i> ${article.ticker}</span>
                        ${sentimentBadge}
                    </div>
                </div>
            `;
        });
        
        document.getElementById('newsFeed').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading news:', error);
        document.getElementById('newsFeed').innerHTML = 
            '<p class="text-danger">Error loading news</p>';
    }
}

// Load Stocks
async function loadStocks() {
    try {
        const stocks = await fetch(`${API_URL}/stocks`).then(r => r.json());
        
        let html = '';
        
        stocks.forEach(stock => {
            const changeClass = stock.change_24h > 0 ? 'positive' : 'negative';
            const changeIcon = stock.change_24h > 0 ? '↑' : '↓';
            
            html += `
                <div class="col-md-4 mb-3">
                    <div class="stock-card">
                        <h5>${stock.ticker}</h5>
                        <p class="text-muted small mb-2">${stock.company}</p>
                        <div class="price">$${stock.current_price.toFixed(2)}</div>
                        <div class="change ${changeClass}">
                            ${changeIcon} ${Math.abs(stock.change_24h || 0).toFixed(2)}%
                        </div>
                    </div>
                </div>
            `;
        });
        
        document.getElementById('stocksGrid').innerHTML = html;
        
    } catch (error) {
        console.error('Error loading stocks:', error);
        document.getElementById('stocksGrid').innerHTML = 
            '<p class="text-danger">Error loading stocks</p>';
    }
}

// Refresh Data
async function refreshData() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Refreshing...';
    
    try {
        await fetch(`${API_URL}/refresh`, { method: 'POST' });
        
        setTimeout(() => {
            loadDashboard();
            loadPredictions();
            loadNews();
            loadStocks();
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Data';
        }, 2000);
        
    } catch (error) {
        console.error('Error refreshing data:', error);
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Data';
    }
}

// Helper Functions
function getSentimentClass(sentiment) {
    if (sentiment === 'Positive') return 'bg-success';
    if (sentiment === 'Negative') return 'bg-danger';
    return 'bg-warning';
}

function getSentimentClassFromScore(score) {
    if (score > 0.1) return 'sentiment-positive';
    if (score < -0.1) return 'sentiment-negative';
    return 'sentiment-neutral';
}
