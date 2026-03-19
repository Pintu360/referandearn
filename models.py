# database/models.py
from sqlalchemy import create_engine, Column, String, BigInteger, Boolean, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """Telegram users"""
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Wallet(Base):
    """Tracked wallets"""
    __tablename__ = 'wallets'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String, unique=True, nullable=False, index=True)
    label = Column(String)
    user_id = Column(String, nullable=False, index=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    balance = Column(Float, default=0)
    balance_sol = Column(Float, default=0)

class Transaction(Base):
    """Transactions from tracked wallets"""
    __tablename__ = 'transactions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    signature = Column(String, unique=True, nullable=False, index=True)
    wallet_address = Column(String, nullable=False, index=True)
    from_address = Column(String)
    to_address = Column(String)
    amount = Column(Float)
    token_address = Column(String)
    token_symbol = Column(String)
    timestamp = Column(DateTime, nullable=False)
    transaction_type = Column(String)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TokenCache(Base):
    """Cached token information"""
    __tablename__ = 'token_cache'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String, unique=True, nullable=False, index=True)
    symbol = Column(String)
    name = Column(String)
    price_usd = Column(Float)
    price_change_24h = Column(Float)
    liquidity_usd = Column(Float)
    volume_24h = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)