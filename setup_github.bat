@echo off
echo ========================================
echo GitHub Repository Setup
echo News Sentiment Based Stock Predictor
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Initialize Git Repository
git init
echo.

echo Step 2: Add all files
git add .
echo.

echo Step 3: Initial commit
git commit -m "Initial commit: News Sentiment Based Stock Predictor with PySpark"
echo.

echo Step 4: Create team-dev branch
git branch team-dev
echo.

echo ========================================
echo Next Steps (Manual):
echo ========================================
echo.
echo 1. Create a new repository on GitHub
echo    Repository name: News-Sentiment-Stock-Predictor
echo.
echo 2. Run these commands (replace YOUR_USERNAME):
echo    git remote add origin https://github.com/YOUR_USERNAME/News-Sentiment-Stock-Predictor.git
echo    git push -u origin main
echo    git push -u origin team-dev
echo.
echo 3. On GitHub, go to Settings ^> Branches
echo    - Set "main" as default branch
echo    - Add branch protection rule for "main":
echo      * Enable "Require pull request reviews before merging"
echo      * Enable "Require status checks to pass before merging"
echo      * Enable "Include administrators" (optional)
echo.
echo 4. Share repository URL with your team
echo    Team members should clone and work on team-dev branch
echo.
echo 5. Add collaborators:
echo    Settings ^> Collaborators ^> Add people
echo.
pause
