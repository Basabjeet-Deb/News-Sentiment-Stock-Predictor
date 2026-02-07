# Contributing Guide

## Branch Structure

- `main` - Production branch (protected, only owner can push)
- `team-dev` - Team development branch (teammates work here)

## Workflow for Team Members

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "News Sentiment Based Stock Predictor"
```

### 2. Switch to Team Branch
```bash
git checkout team-dev
```

### 3. Make Your Changes
- Edit notebooks or add new files
- Test your changes locally with Spark cluster

### 4. Commit and Push
```bash
git add .
git commit -m "Description of your changes"
git push origin team-dev
```

### 5. Create Pull Request
- Go to GitHub repository
- Create Pull Request from `team-dev` to `main`
- Owner will review and merge

## Workflow for Owner (Master Node)

### Review Team Changes
```bash
git checkout team-dev
git pull origin team-dev
# Review changes
```

### Merge to Main
```bash
git checkout main
git merge team-dev
git push origin main
```

### Sync Team Branch with Main
```bash
git checkout team-dev
git merge main
git push origin team-dev
```

## Important Notes

- **Always work on `team-dev` branch** (teammates)
- **Never push directly to `main`** (teammates)
- Pull latest changes before starting work: `git pull origin team-dev`
- Communicate with team about conflicts
- Test your code with the Spark cluster before pushing

## File Structure

```
News Sentiment Based Stock Predictor/
├── cluster/              # Cluster setup (master & workers)
├── notebooks/            # Analysis notebooks
├── data/                 # Dataset storage
└── README.md            # Project documentation
```
