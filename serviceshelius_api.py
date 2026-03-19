# services/helius_api.py
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config import config

class HeliusAPI:
    """Helius API service for enhanced transaction data"""
    
    def __init__(self):
        self.api_key = config.HELIUS_API_KEY
        self.base_url = config.HELIUS_API_URL
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            print("✅ Helius API initialized")
        else:
            print("⚠️ Helius API disabled (no API key)")
    
    async def get_transactions(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get enhanced transactions for an address"""
        if not self.enabled:
            return []
        
        url = f"{self.base_url}/addresses/{address}/transactions"
        params = {
            'api-key': self.api_key,
            'limit': min(limit, 100)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_transactions(data)
                    else:
                        print(f"⚠️ Helius API error: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ Helius API error: {e}")
            return []
    
    async def get_parsed_transaction(self, signature: str) -> Optional[Dict[str, Any]]:
        """Get parsed transaction by signature"""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/transactions"
        params = {'api-key': self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, json=[signature]) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            return self._parse_transaction(data[0])
                    return None
                    
        except Exception as e:
            print(f"❌ Helius API error: {e}")
            return None
    
    async def get_token_metadata(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Get token metadata"""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/token-metadata"
        params = {
            'api-key': self.api_key,
            'mint': mint_address
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
                    
        except Exception as e:
            print(f"❌ Helius API error: {e}")
            return None
    
    def _parse_transactions(self, transactions: List[Dict]) -> List[Dict[str, Any]]:
        """Parse multiple transactions"""
        parsed = []
        for tx in transactions:
            parsed_tx = self._parse_transaction(tx)
            if parsed_tx:
                parsed.append(parsed_tx)
        return parsed
    
    def _parse_transaction(self, tx: Dict) -> Dict[str, Any]:
        """Parse a single transaction"""
        try:
            parsed = {
                'signature': tx.get('signature'),
                'timestamp': datetime.fromtimestamp(tx.get('timestamp', 0)),
                'type': tx.get('type', 'UNKNOWN'),
                'fee': tx.get('fee', 0) / 1_000_000_000,
                'status': tx.get('status', 'unknown'),
                'description': tx.get('description', '')
            }
            
            # Check for token transfers
            if 'tokenTransfers' in tx and tx['tokenTransfers']:
                transfers = []
                for transfer in tx['tokenTransfers'][:3]:  # Limit to first 3
                    transfers.append({
                        'from': transfer.get('fromUserAccount'),
                        'to': transfer.get('toUserAccount'),
                        'amount': transfer.get('tokenAmount'),
                        'mint': transfer.get('mint'),
                        'symbol': transfer.get('symbol', 'UNKNOWN')
                    })
                parsed['token_transfers'] = transfers
            
            # Check for native SOL transfers
            if 'nativeTransfers' in tx and tx['nativeTransfers']:
                transfers = []
                for transfer in tx['nativeTransfers'][:3]:
                    transfers.append({
                        'from': transfer.get('fromUserAccount'),
                        'to': transfer.get('toUserAccount'),
                        'amount': transfer.get('amount', 0) / 1_000_000_000
                    })
                parsed['sol_transfers'] = transfers
            
            return parsed
            
        except Exception as e:
            print(f"❌ Error parsing Helius transaction: {e}")
            return None

# Create singleton instance
helius_api = HeliusAPI()