# services/solana_rpc.py
from solana.rpc.api import Client
from solana.publickey import PublicKey
from solders.signature import Signature
from typing import List, Dict, Any, Optional
from datetime import datetime
import base58

from config import config

class SolanaRPC:
    """Core Solana RPC service for basic blockchain interactions"""
    
    def __init__(self):
        self.client = Client(config.SOLANA_RPC_URL)
        print(f"✅ Solana RPC initialized: {config.SOLANA_RPC_URL}")
    
    def validate_address(self, address: str) -> bool:
        """Validate if a string is a valid Solana address"""
        try:
            if len(address) not in [32, 44, 43]:
                return False
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except:
            return False
    
    def get_balance(self, address: str) -> float:
        """Get SOL balance for a wallet in SOL (not lamports)"""
        try:
            pubkey = PublicKey(address)
            response = self.client.get_balance(pubkey)
            
            if response and 'result' in response:
                # Convert lamports to SOL (1 SOL = 1e9 lamports)
                lamports = response['result']['value']
                return lamports / 1_000_000_000
            return 0.0
            
        except Exception as e:
            print(f"❌ Error getting balance for {address[:8]}...: {e}")
            return 0.0
    
    def get_multiple_balances(self, addresses: List[str]) -> Dict[str, float]:
        """Get balances for multiple addresses"""
        results = {}
        for address in addresses:
            results[address] = self.get_balance(address)
        return results
    
    def get_recent_transactions(self, address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transaction signatures for an address"""
        try:
            pubkey = PublicKey(address)
            response = self.client.get_signatures_for_address(pubkey, limit=limit)
            
            transactions = []
            if response and 'result' in response:
                for sig_info in response['result']:
                    transactions.append({
                        'signature': sig_info['signature'],
                        'slot': sig_info['slot'],
                        'timestamp': datetime.fromtimestamp(sig_info['blockTime']),
                        'status': 'success' if not sig_info.get('err') else 'failed'
                    })
            
            return transactions
            
        except Exception as e:
            print(f"❌ Error getting transactions for {address[:8]}...: {e}")
            return []
    
    def get_transaction_details(self, signature: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific transaction"""
        try:
            response = self.client.get_transaction(signature, encoding="jsonParsed")
            
            if response and 'result' in response:
                tx = response['result']
                return self._parse_transaction(tx, signature)
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting transaction details: {e}")
            return None
    
    def _parse_transaction(self, tx_data: Dict, signature: str) -> Dict[str, Any]:
        """Parse raw transaction data"""
        try:
            meta = tx_data.get('meta', {})
            transaction = tx_data.get('transaction', {})
            
            # Basic info
            parsed = {
                'signature': signature,
                'slot': tx_data.get('slot', 0),
                'timestamp': datetime.fromtimestamp(tx_data.get('blockTime', 0)),
                'fee': meta.get('fee', 0) / 1_000_000_000,  # Convert to SOL
                'status': 'success' if not meta.get('err') else 'failed',
                'logs': meta.get('logMessages', [])
            }
            
            # Try to extract transfer info
            if 'message' in transaction:
                message = transaction['message']
                if 'instructions' in message:
                    for ix in message['instructions']:
                        if 'parsed' in ix:
                            parsed_ix = ix['parsed']
                            if parsed_ix.get('type') == 'transfer':
                                info = parsed_ix.get('info', {})
                                parsed['transfer'] = {
                                    'from': info.get('source'),
                                    'to': info.get('destination'),
                                    'amount': info.get('lamports', 0) / 1_000_000_000
                                }
            
            return parsed
            
        except Exception as e:
            print(f"❌ Error parsing transaction: {e}")
            return {
                'signature': signature,
                'error': str(e)
            }
    
    def get_token_accounts(self, address: str) -> List[Dict[str, Any]]:
        """Get all token accounts owned by an address"""
        try:
            pubkey = PublicKey(address)
            token_program = PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            
            response = self.client.get_token_accounts_by_owner(
                pubkey,
                {"programId": token_program}
            )
            
            token_accounts = []
            if response and 'result' in response:
                for account in response['result']['value']:
                    try:
                        account_data = account['account']['data']['parsed']['info']
                        token_accounts.append({
                            'mint': account_data['mint'],
                            'owner': account_data['owner'],
                            'amount': account_data['tokenAmount']['uiAmount'],
                            'decimals': account_data['tokenAmount']['decimals']
                        })
                    except:
                        continue
            
            return token_accounts
            
        except Exception as e:
            print(f"❌ Error getting token accounts: {e}")
            return []

# Create singleton instance
solana_rpc = SolanaRPC()