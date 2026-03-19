# database/crud.py
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models import Base, User, Wallet, Transaction, TokenCache
from config import config

class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        self.engine = create_engine(
            config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.Session()
    
    # ========== User Operations ==========
    
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        """Get existing user or create new one"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
                print(f"✅ New user created: {telegram_id}")
            
            return user
        finally:
            session.close()
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(telegram_id=telegram_id).first()
        finally:
            session.close()
    
    # ========== Wallet Operations ==========
    
    def add_wallet(self, telegram_id: int, user_id: str, address: str, label: str = None) -> Wallet:
        """Add a wallet to tracking"""
        session = self.get_session()
        try:
            # Check if wallet already exists
            existing = session.query(Wallet).filter_by(address=address).first()
            
            if existing:
                if existing.user_id != user_id:
                    raise Exception("Wallet already tracked by another user")
                if not existing.is_active:
                    existing.is_active = True
                    session.commit()
                return existing
            
            # Create new wallet
            wallet = Wallet(
                address=address,
                label=label,
                user_id=user_id,
                telegram_id=telegram_id
            )
            session.add(wallet)
            session.commit()
            print(f"✅ Wallet added: {address[:8]}... for user {telegram_id}")
            return wallet
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_wallets(self, user_id: str) -> List[Wallet]:
        """Get all active wallets for a user"""
        session = self.get_session()
        try:
            return session.query(Wallet)\
                .filter_by(user_id=user_id, is_active=True)\
                .order_by(Wallet.added_at.desc())\
                .all()
        finally:
            session.close()
    
    def get_all_active_wallets(self) -> List[Wallet]:
        """Get all active wallets across all users"""
        session = self.get_session()
        try:
            return session.query(Wallet).filter_by(is_active=True).all()
        finally:
            session.close()
    
    def update_wallet_balance(self, address: str, balance_sol: float):
        """Update wallet balance"""
        session = self.get_session()
        try:
            wallet = session.query(Wallet).filter_by(address=address).first()
            if wallet:
                wallet.balance_sol = balance_sol
                wallet.last_checked = datetime.utcnow()
                session.commit()
        finally:
            session.close()
    
    def remove_wallet(self, user_id: str, address: str):
        """Soft delete a wallet (deactivate)"""
        session = self.get_session()
        try:
            wallet = session.query(Wallet).filter_by(
                user_id=user_id, 
                address=address
            ).first()
            
            if wallet:
                wallet.is_active = False
                session.commit()
                print(f"✅ Wallet removed: {address[:8]}...")
        finally:
            session.close()
    
    def get_wallet_count(self, user_id: str) -> int:
        """Get number of wallets tracked by user"""
        session = self.get_session()
        try:
            return session.query(Wallet)\
                .filter_by(user_id=user_id, is_active=True)\
                .count()
        finally:
            session.close()
    
    # ========== Transaction Operations ==========
    
    def add_transaction(self, tx_data: Dict[str, Any]) -> Optional[Transaction]:
        """Add a transaction to database"""
        session = self.get_session()
        try:
            # Check if exists
            existing = session.query(Transaction)\
                .filter_by(signature=tx_data['signature'])\
                .first()
            
            if existing:
                return existing
            
            # Create new transaction
            transaction = Transaction(**tx_data)
            session.add(transaction)
            session.commit()
            return transaction
            
        except Exception as e:
            session.rollback()
            print(f"Error adding transaction: {e}")
            return None
        finally:
            session.close()
    
    def get_unprocessed_transactions(self, limit: int = 100) -> List[Transaction]:
        """Get transactions that haven't been processed"""
        session = self.get_session()
        try:
            return session.query(Transaction)\
                .filter_by(is_processed=False)\
                .order_by(Transaction.timestamp)\
                .limit(limit)\
                .all()
        finally:
            session.close()
    
    def mark_transaction_processed(self, signature: str):
        """Mark transaction as processed"""
        session = self.get_session()
        try:
            tx = session.query(Transaction)\
                .filter_by(signature=signature)\
                .first()
            if tx:
                tx.is_processed = True
                session.commit()
        finally:
            session.close()
    
    # ========== Token Cache Operations ==========
    
    def get_cached_token(self, address: str) -> Optional[TokenCache]:
        """Get cached token data"""
        session = self.get_session()
        try:
            return session.query(TokenCache)\
                .filter_by(address=address)\
                .first()
        finally:
            session.close()
    
    def update_token_cache(self, token_data: Dict[str, Any]) -> TokenCache:
        """Update or create token cache"""
        session = self.get_session()
        try:
            token = session.query(TokenCache)\
                .filter_by(address=token_data['address'])\
                .first()
            
            if not token:
                token = TokenCache(**token_data)
                session.add(token)
            else:
                for key, value in token_data.items():
                    if key != 'address':
                        setattr(token, key, value)
                token.last_updated = datetime.utcnow()
            
            session.commit()
            return token
            
        finally:
            session.close()

# Create global database manager instance
db_manager = DatabaseManager()