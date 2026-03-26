from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User as UserModel, Portfolio, Transaction
from config import Config
import yfinance as yf
import threading
import time
import os

app = Flask(__name__, static_folder='.', template_folder='templates')
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js')

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.username
        self.username = user_data.username

@login_manager.user_loader
def load_user(user_id):
    user_data = UserModel.find_user_by_username(user_id)
    if user_data:
        return User(user_data)
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if UserModel.find_user_by_username(username):
            flash('Username already exists')
            return redirect(url_for('register'))
        if UserModel.find_user_by_email(email):
            flash('Email already registered')
            return redirect(url_for('register'))

        created_user = UserModel.create_user(username, email, password)
        if not created_user:
            flash('Registration failed: duplicate username or email')
            return redirect(url_for('register'))

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = UserModel.find_user_by_username(username)
        if user_data and UserModel.check_password(user_data, password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
        return redirect(url_for('login'))
    return render_template('login.html')

from flask import Flask, request, render_template, redirect, url_for, flash

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    
    # Logic: In a real project, you would check your database here
    # and send a real email using Flask-Mail.
    print(f"Reset request received for: {email}")

    # For now, we simulate success and send the user back to login
    flash(f"Success! A reset link has been sent to {email}")
    return redirect(url_for('login')) # Ensure 'login' matches your login function name

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/get_stock_price/<symbol>')
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        # Fetch the most recent price
        price = stock.fast_info['last_price'] 
        return jsonify({"symbol": symbol, "price": round(price, 2)})
    except Exception as e:
        return jsonify({"error": "Invalid Symbol"}), 400

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/api/portfolio')
@login_required
def api_portfolio():
    portfolio = Portfolio.get_portfolio(current_user.id)
    stocks = portfolio.get('stocks', {})
    return jsonify(list(stocks.items()))

@app.route('/api/transactions')
@login_required
def api_transactions():
    transactions = Transaction.get_transactions(current_user.id)
    return jsonify(transactions)

@app.route('/api/profile')
@login_required
def api_profile():
    user_data = UserModel.find_user_by_username(current_user.username)
    return jsonify({
        'username': user_data.username,
        'email': user_data.email,
        'balance': user_data.balance
    })

@app.route('/api/deposit', methods=['POST'])
@login_required
def api_deposit():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    method = data.get('method', '')
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Invalid amount'}), 400
    if method not in ['UPI', 'Google Pay', 'PhonePe', 'Paytm']:
        return jsonify({'success': False, 'error': 'Invalid method'}), 400

    UserModel.update_balance(current_user.username, amount)
    return jsonify({'success': True, 'balance': UserModel.find_user_by_username(current_user.username).balance})

@app.route('/api/trade', methods=['POST'])
@login_required
def api_trade():
    data = request.get_json()
    symbol = data['symbol']
    quantity = int(data['quantity'])
    action = data['action']
    if action == 'buy':
        return buy_logic(symbol, quantity)
    elif action == 'sell':
        return sell_logic(symbol, quantity)
    return jsonify({'error': 'Invalid action'}), 400

def buy_logic(symbol, quantity):
    mock_prices = {'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0}
    price = mock_prices.get(symbol.upper(), 100.0)
    total = price * quantity
    user_data = UserModel.find_user_by_username(current_user.username)
    if user_data.balance < total:
        return jsonify({'error': 'Insufficient balance'})
    UserModel.update_balance(current_user.username, -total)
    portfolio = Portfolio.get_portfolio(current_user.id)
    stocks = portfolio.get('stocks', {})
    stocks[symbol] = stocks.get(symbol, 0) + quantity
    Portfolio.update_portfolio(current_user.id, stocks)
    Transaction.add_transaction(current_user.id, symbol, quantity, price, 'buy')
    return jsonify({'message': 'Buy successful'})

def sell_logic(symbol, quantity):
    portfolio = Portfolio.get_portfolio(current_user.id)
    stocks = portfolio.get('stocks', {})
    if stocks.get(symbol, 0) < quantity:
        return jsonify({'error': 'Insufficient stocks'})
    mock_prices = {'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0}
    price = mock_prices.get(symbol.upper(), 100.0)
    total = price * quantity
    UserModel.update_balance(current_user.username, total)
    stocks[symbol] -= quantity
    if stocks[symbol] == 0:
        del stocks[symbol]
    Portfolio.update_portfolio(current_user.id, stocks)
    Transaction.add_transaction(current_user.id, symbol, quantity, price, 'sell')
    return jsonify({'message': 'Sell successful'})

@app.route('/api/stock')
def api_stock():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return {'error': 'symbol parameter required'}, 400
    symbol = symbol.upper()
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d')
        if df.empty:
            return {'symbol': symbol, 'price': None, 'error': 'No data'}, 404
        price = float(df['Close'].iloc[-1])
        return {'symbol': symbol, 'price': price}
    except Exception as e:
        return {'symbol': symbol, 'price': None, 'error': str(e)}, 500

@app.route('/api/stock-history')
def api_stock_history():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '1mo')
    interval_map = {
        '1d': '5m',
        '5d': '30m',
        '1mo': '1h',
        '3mo': '1d',
        '6mo': '1d',
        '1y': '1d',
        '5y': '1wk'
    }
    if not symbol:
        return {'error': 'symbol parameter required'}, 400
    if period not in interval_map:
        return {'error': 'invalid period'}, 400

    interval = interval_map.get(period, '1d')
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return {'symbol': symbol, 'data': []}

        data = []
        for idx, row in df.iterrows():
            data.append({
                'datetime': idx.strftime('%Y-%m-%d %H:%M:%S'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            })

        return {'symbol': symbol, 'data': data}
    except Exception as e:
        return {'symbol': symbol, 'data': [], 'error': str(e)}, 500

# Real-time stock updates
stock_symbols = ['AAPL', 'GOOGL', 'MSFT']

def update_stocks():
    while True:
        data = {}
        for symbol in stock_symbols:
            mock_prices = {'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0}
            data[symbol] = mock_prices.get(symbol, 0)
        socketio.emit('stock_update', data)
        time.sleep(10)

threading.Thread(target=update_stocks, daemon=True).start()

@socketio.on('connect')
def handle_connect():
    mock_prices = {'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0}
    data = {symbol: mock_prices.get(symbol, 0) for symbol in stock_symbols}
    emit('stock_update', data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)