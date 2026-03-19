# services/dexscreener_api.py
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from cachetools import TTLCache
from datetime import datetime

from config import config

class DexScreenerAPI:
    """DexScreener API service for token prices and pairs"""
    
    def __init__(self):
        self.base_url = config.DEXSCREENER_API_URL
        # Cache prices for 1 minute to avoid rate limits
        self.price_cache = TTLCache(maxsize=200, ttl=60)
        self.search_cache = TTLCache(maxsize=50, ttl=300)
        print("✅ DexScreener API initialized")
    
    async def get_token_price(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token price and liquidity info"""
        # Check cache first
        cache_key = f"price_{token_address}"
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tokens/{token_address}"
                async with session.get(url) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if not data.get('pairs'):
                            return None
                        
                        # Filter for Solana pairs only
                        solana_pairs = [
                            pair for pair in data['pairs']
                            if pair.get('chainId') == 'solana'
                        ]
                        
                        if not solana_pairs:
                            return None
                        
                        # Get the pair with highest liquidity
                        best_pair = max(
                            solana_pairs,
                            key=lambda x: float(x.get('liquidity', {}).get('usd', 0))
                        )
                        
                        # Parse the data
                        result = {
                            'address': token_address,
                            'price_usd': float(best_pair.get('priceUsd', 0)),
                            'price_sol': float(best_pair.get('priceNative', 0)),
                            'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
                            'liquidity_usd': float(best_pair.get('liquidity', {}).get('usd', 0)),
                            'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                            'dex': best_pair.get('dexId', 'unknown'),
                            'pair_address': best_pair.get('pairAddress'),
                            'base_token': best_pair.get('baseToken', {}),
                            'quote_token': best_pair.get('quoteToken', {}),
                            'url': f"https://dexscreener.com/solana/{best_pair.get('pairAddress')}",
                            'fetched_at': datetime.utcnow().isoformat()
                        }
                        
                        # Cache the result
                        self.price_cache[cache_key] = result
                        return result
                    
                    return None
                    
        except Exception as e:
            print(f"❌ DexScreener API error: {e}")
            return None
    
    async def search_tokens(self, query: str) -> List[Dict[str, Any]]:
        """Search for tokens by symbol or name"""
        # Check cache
        cache_key = f"search_{query.lower()}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search"
                params = {'q': query}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        results = []
                        if data.get('pairs'):
                            # Track unique tokens by address
                            seen_addresses = set()
                            
                            for pair in data['pairs']:
                                if pair.get('chainId') != 'solana':
                                    continue
                                
                                base_token = pair.get('baseToken', {})
                                token_address = base_token.get('address')
                                
                                if token_address and token_address not in seen_addresses:
                                    seen_addresses.add(token_address)
                                    
                                    results.append({
                                        'address': token_address,
                                        'symbol': base_token.get('symbol', 'UNKNOWN'),
                                        'name': base_token.get('name', 'Unknown'),
                                        'price_usd': float(pair.get('priceUsd', 0)),
                                        'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                                        'dex': pair.get('dexId', 'unknown'),
                                        'url': f"https://dexscreener.com/solana/{pair.get('pairAddress')}"
                                    })
                                    
                                    if len(results) >= 20:
                                        break
                        
                        # Sort by liquidity
                        results.sort(key=lambda x: x.get('liquidity_usd', 0), reverse=True)
                        
                        # Cache results
                        self.search_cache[cache_key] = results[:10]
                        return results[:10]
                    
                    return []
                    
        except Exception as e:
            print(f"❌ DexScreener search error: {e}")
            return []
    
    async def get_token_pairs(self, token_address: str) -> List[Dict[str, Any]]:
        """Get all trading pairs for a token"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tokens/{token_address}"
                async with session.get(url) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        pairs = []
                        if data.get('pairs'):
                            for pair in data['pairs']:
                                if pair.get('chainId') == 'solana':
                                    pairs.append({
                                        'dex': pair.get('dexId', 'unknown'),
                                        'pair_address': pair.get('pairAddress'),
                                        'price_usd': float(pair.get('priceUsd', 0)),
                                        'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                                        'url': f"https://dexscreener.com/solana/{pair.get('pairAddress')}"
                                    })
                            
                            # Sort by liquidity
                            pairs.sort(key=lambda x: x.get('liquidity_usd', 0), reverse=True)
                        
                        return pairs
                    
                    return []
                    
        except Exception as e:
            print(f"❌ DexScreener pairs error: {e}")
            return []

# Create singleton instance
dexscreener_api = DexScreenerAPI()