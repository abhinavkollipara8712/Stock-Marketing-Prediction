from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    balance = db.Column(db.Float, default=10000.0)

    @staticmethod
    def create_user(username, email, password):
        from sqlalchemy.exc import IntegrityError
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        try:
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            return None

    @staticmethod
    def find_user_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_user_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def check_password(user, password):
        return check_password_hash(user.password, password)

    @staticmethod
    def update_balance(username, amount):
        user = User.query.filter_by(username=username).first()
        if user:
            user.balance += amount
            db.session.commit()

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(150), nullable=False)
    stocks = db.Column(db.Text, default='{}')  # JSON string

    @staticmethod
    def get_portfolio(user_id):
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=user_id)
            db.session.add(portfolio)
            db.session.commit()
        import json
        stocks = json.loads(portfolio.stocks) if portfolio.stocks else {}
        return {'user_id': user_id, 'stocks': stocks}

    @staticmethod
    def update_portfolio(user_id, stocks):
        import json
        portfolio = Portfolio.query.filter_by(user_id=user_id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=user_id)
            db.session.add(portfolio)
        portfolio.stocks = json.dumps(stocks)
        db.session.commit()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(150), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def add_transaction(user_id, symbol, quantity, price, type_):
        transaction = Transaction(user_id=user_id, symbol=symbol, quantity=quantity, price=price, type=type_)
        db.session.add(transaction)
        db.session.commit()

    @staticmethod
    def get_transactions(user_id):
        transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
        return [{'symbol': t.symbol, 'quantity': t.quantity, 'price': t.price, 'action': t.type, 'timestamp': t.timestamp.isoformat()} for t in transactions]