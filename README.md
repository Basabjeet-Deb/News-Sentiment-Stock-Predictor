# News Sentiment Based Stock Predictor

Distributed machine learning on Spark cluster for news sentiment analysis and stock prediction using PySpark.

## 🤝 Team Collaboration

This project uses a collaborative Git workflow:

- **`main` branch**: Production code (protected, owner only)
- **`team-dev` branch**: Development branch for all team members

📖 See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed workflow instructions.

## 📁 Project Structure

```
News Sentiment Based Stock Predictor/
├── cluster/              # Cluster setup files
│   ├── master.ipynb      # Start Spark master node
│   ├── worker.ipynb      # Start worker nodes (for teammates)
│   └── start_master.bat  # Quick start master script
│
├── notebooks/            # Analysis notebooks
│   ├── fetch_data.ipynb  # Fetch news data from GDELT
│   └── classification.ipynb  # News classification with ML
│
└── data/                 # Dataset storage
    └── gdelt_english_news.csv
```

## 🚀 Quick Start

### 1. Start the Master Node (Owner)
- Run `cluster/start_master.bat` OR
- Open `cluster/master.ipynb` and run cells

**Master URL**: `spark://192.168.1.5:7077`  
**Web UI**: `http://localhost:8080`

### 2. Connect Workers (Teammates)
- Share `cluster/worker.ipynb` with teammates
- They run it on their machines to join the cluster
- Verify connection on Web UI

### 3. Fetch Data
- Open `notebooks/fetch_data.ipynb`
- Run cells to download news articles from GDELT

### 4. Run Classification
- Open `notebooks/classification.ipynb`
- Run cells to analyze and classify news with distributed ML

## 📋 Requirements

- Python 3.11+
- PySpark
- Apache Spark installed at `C:/spark`
- Network connectivity for cluster mode
- Git for version control

## 🔧 Setup GitHub Repository

1. Run `setup_github.bat` to initialize Git
2. Create repository on GitHub: `News-Sentiment-Stock-Predictor`
3. Follow the instructions in the script output
4. Add team members as collaborators
5. Protect `main` branch (require PR reviews)

## 👥 Team Workflow

**Team Members:**
```bash
git clone <repo-url>
git checkout team-dev
# Make changes
git add .
git commit -m "Your changes"
git push origin team-dev
# Create Pull Request on GitHub
```

**Owner (Master Node):**
```bash
git checkout team-dev
git pull origin team-dev
# Review changes
git checkout main
git merge team-dev
git push origin main
```

## 📊 Features

- Distributed data processing with PySpark
- Real-time news fetching from GDELT API
- Sentiment analysis on news articles
- Stock prediction based on news sentiment
- Collaborative development workflow
- Scalable cluster architecture

## 🛠️ Tech Stack

- **PySpark**: Distributed computing
- **Apache Spark**: Cluster management
- **GDELT API**: News data source
- **Jupyter Notebooks**: Interactive development
- **Git**: Version control

---

**Master Node Owner**: Manages cluster and merges team contributions  
**Team Members**: Develop on `team-dev` branch and submit PRs
