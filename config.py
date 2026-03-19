# config.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Solana RPC (Primary)
    SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    
    # Helius API
    HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
    HELIUS_RPC_URL = f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}" if HELIUS_API_KEY else None
    HELIUS_API_URL = "https://api.helius.xyz/v0"
    
    # Solscan API
    SOLSCAN_API_KEY = os.getenv("SOLSCAN_API_KEY")
    SOLSCAN_API_URL = "https://api.solscan.io"
    
    # DexScreener (No API key needed)
    DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex"
    
    # Bot Settings
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
    MAX_WALLETS_PER_USER = int(os.getenv("MAX_WALLETS_PER_USER", "100"))
    PORT = int(os.getenv("PORT", "10000"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        missing = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        
        if not cls.DATABASE_URL:
            missing.append("DATABASE_URL")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Optional API warnings
        if not cls.HELIUS_API_KEY:
            print("⚠️ Warning: HELIUS_API_KEY not set. Enhanced transaction data will be limited.")
        
        if not cls.SOLSCAN_API_KEY:
            print("⚠️ Warning: SOLSCAN_API_KEY not set. Token holder data will be unavailable.")

# Create config instance
config = Config()

# Validate on import
config.validate()