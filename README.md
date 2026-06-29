# 🏆 World Cup 2026 Betting Dashboard

A interactive Streamlit dashboard to track predictions, calculate scores, and display group-stage and knockout (Round of 32) progress for the World Cup 2026.

---

## 🚀 How to Start the Dashboard

### 1. Prerequisites
Make sure you have **Python 3.9+** installed on your system.

### 2. Install Dependencies
Navigate to the project root directory and install the required packages:
```bash
pip install -r requirements.txt
```
*(Note: To parse the Excel prediction sheet, pandas requires `openpyxl`. Install it if you haven't already: `pip install openpyxl`)*

### 3. Fetch the Latest Results
Run the scraper script to fetch the latest match results from Wikipedia and map them to player predictions:
```bash
python3 scraper.py
```
This will automatically generate/update `real_results.json`.

### 4. Run the Streamlit Dashboard
Launch the dashboard locally:
```bash
streamlit run streamlit_app.py
```
Once started, the dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 🎯 Scoring System

Points are dynamically calculated based on actual match results compared against player predictions:
* **3 Points**: Exact Score Match (e.g. predicted `2 - 1`, actual `2 - 1`).
* **2 Points**: Correct Winner and Goal Difference (e.g. predicted `3 - 1`, actual `2 - 0`).
* **1 Point**: Correct Winner/Outcome only (e.g. predicted `1 - 0`, actual `2 - 1`).
* **0 Points**: Incorrect Winner/Outcome or missing prediction (indicated as **No Bet**).

---

## 📊 Features

* **🏆 Leaderboard**: Real-time rank of all players, points visualizer, and an "Exact Score Snipers" table.
* **📈 Point Progression Race**: Interactive line chart showing cumulative points progress chronologically across matches.
* **📊 Player Details**: Individual breakdown of predictions, points won, and an **Accuracy Breakdown** donut chart.
* **⚔️ Head-to-Head Comparison**: Select any two players to compare their overlapping predictions and head-to-head point tallies.
* **🧠 Deep Insights**: Features the **Contrarian Award** (scoring points on an outcome predicted by <15% of players) and **Crowd vs Reality** match-by-match metrics.
