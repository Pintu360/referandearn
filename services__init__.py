# services/__init__.py
from .solana_rpc import SolanaRPC
from .helius_api import HeliusAPI
from .solscan_api import SolscanAPI
from .dexscreener_api import DexScreenerAPI

# Initialize service instances
solana_rpc = SolanaRPC()
helius_api = HeliusAPI()
solscan_api = SolscanAPI()
dexscreener_api = DexScreenerAPI()

__all__ = [
    'solana_rpc',
    'helius_api', 
    'solscan_api',
    'dexscreener_api'
]