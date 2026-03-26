# TradeX - Stock Trading Web App

A complete stock trading web application (demo) built with:

- Frontend: HTML, CSS (Tailwind), JavaScript, Chart.js
- Backend: Python Flask + Flask-Login + Flask-SocketIO
- Database: SQLite via SQLAlchemy
- Market data: yfinance API

## Features

- User registration and login
- Authenticated dashboard
- Portfolio tracking
- Buy/Sell mock trading
- Transaction logging
- Real-time market updates (via SocketIO mock data)
- Market chart with candlestick + EMA
- Time frame selection: daily/weekly/monthly/yearly
- Responsive UI and page navigation

## Requirements

- Python >= 3.10
- Packages from `requirements.txt`

## Install

```bash
cd "C:\Users\prane\OneDrive\Desktop\Mini Project"
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
# or venv\Scripts\activate      # cmd
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Api Endpoints

- `/register` (GET/POST)
- `/login` (GET/POST)
- `/logout`
- `/dashboard`
- `/profile`
- `/api/portfolio`
- `/api/transactions`
- `/api/profile`
- `/api/trade` (POST)
- `/api/stock` (GET)
- `/api/stock-history` (GET)

## Quick usage

1. Register user
2. Login
3. Dashboard: click NIFTY/BANKNIFTY/SENSEX card to load chart
4. Choose timeframe: `1d`, `5d`, `1mo`, `1y`
5. Quick trade or regular trade

## Notes

- Stocks and prices are mocked for trading calculations.
- `yfinance` is used for price history chart.
- Live personal trading is not real; this is a simulation.
