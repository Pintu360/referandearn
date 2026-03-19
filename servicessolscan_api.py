# services/solscan_api.py
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import config

class SolscanAPI:
    """Solscan API service for token and holder data"""
    
    def __init__(self):
        self.api_key = config.SOLSCAN_API_KEY
        self.base_url = config.SOLSCAN_API_URL
        self.enabled = bool(self.api_key)
        
        self.headers = {
            'Accept': 'application/json',
            'token': self.api_key
        } if self.enabled else {'Accept': 'application/json'}
        
        if self.enabled:
            print("✅ Solscan API initialized")
        else:
            print("⚠️ Solscan API disabled (no API key)")
    
    async def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token metadata"""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/token/meta"
        params = {'address': token_address}
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('data', {})
                    return None
                    
        except Exception as e:
            print(f"❌ Solscan API error: {e}")
            return None
    
    async def get_token_holders(self, token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get token holders list"""
        if not self.enabled:
            return []
        
        url = f"{self.base_url}/token/holders"
        params = {
            'address': token_address,
            'limit': min(limit, 100),
            'offset': 0
        }
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('data', [])
                    return []
                    
        except Exception as e:
            print(f"❌ Solscan API error: {e}")
            return []
    
    async def get_token_market(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token market data"""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/market/token/{token_address}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('data', {})
                    return None
                    
        except Exception as e:
            print(f"❌ Solscan API error: {e}")
            return None
    
    async def get_account_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/account/{address}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('data', {})
                    return None
                    
        except Exception as e:
            print(f"❌ Solscan API error: {e}")
            return None
    
    async def get_account_transactions(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get account transactions"""
        if not self.enabled:
            return []
        
        url = f"{self.base_url}/account/transactions"
        params = {
            'address': address,
            'limit': min(limit, 50),
            'sort': 'blocktime'
        }
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            return data.get('data', [])
                    return []
                    
        except Exception as e:
            print(f"❌ Solscan API error: {e}")
            return []

# Create singleton instance
solscan_api = SolscanAPI()