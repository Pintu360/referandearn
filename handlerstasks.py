# handlers/tasks.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database.crud import db_manager
from services import solana_rpc, helius_api, dexscreener_api
from utils.helpers import format_address, format_usd

class BackgroundTasks:
    """Background tasks for monitoring wallets and processing transactions"""
    
    def __init__(self, application):
        self.application = application
        self.is_running = False
        self.check_interval = 60  # seconds
        self.whale_threshold = 100_000  # $100k USD
        
    async def start(self):
        """Start all background tasks"""
        self.is_running = True
        
        # Start monitoring tasks
        asyncio.create_task(self.wallet_monitor())
        asyncio.create_task(self.transaction_processor())
        asyncio.create_task(self.cleanup_task())
        
        print("✅ Background tasks started")
    
    async def stop(self):
        """Stop all background tasks"""
        self.is_running = False
        print("🛑 Background tasks stopped")
    
    # ========== Main Monitoring Tasks ==========
    
    async def wallet_monitor(self):
        """Monitor tracked wallets for balance changes"""
        while self.is_running:
            try:
                # Get all active wallets
                wallets = db_manager.get_all_active_wallets()
                
                if not wallets:
                    await asyncio.sleep(self.check_interval)
                    continue
                
                print(f"🔄 Checking {len(wallets)} wallets...")
                
                # Process in batches of 20 to avoid rate limits
                batch_size = 20
                for i in range(0, len(wallets), batch_size):
                    batch = wallets[i:i + batch_size]
                    
                    # Check each wallet in batch
                    for wallet in batch:
                        await self._check_wallet_balance(wallet)
                        await asyncio.sleep(2)  # Delay between checks
                    
                    # Delay between batches
                    await asyncio.sleep(5)
                
                # Wait before next full check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Error in wallet monitor: {e}")
                await asyncio.sleep(10)
    
    async def transaction_processor(self):
        """Process new transactions and detect whale movements"""
        while self.is_running:
            try:
                # Get unprocessed transactions from database
                # This would be expanded with actual transaction storage
                
                # For now, just check recent transactions for tracked wallets
                wallets = db_manager.get_all_active_wallets()
                
                for wallet in wallets[:10]:  # Limit to 10 wallets per cycle
                    await self._check_recent_transactions(wallet)
                    await asyncio.sleep(3)
                
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                print(f"❌ Error in transaction processor: {e}")
                await asyncio.sleep(10)
    
    async def cleanup_task(self):
        """Clean up old data periodically"""
        while self.is_running:
            try:
                # Run cleanup once per day
                await asyncio.sleep(86400)  # 24 hours
                
                print("🧹 Running cleanup task...")
                # Add cleanup logic here
                
            except Exception as e:
                print(f"❌ Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    # ========== Wallet Monitoring Helpers ==========
    
    async def _check_wallet_balance(self, wallet):
        """Check individual wallet balance and alert on changes"""
        try:
            # Get current balance
            new_balance = solana_rpc.get_balance(wallet.address)
            old_balance = wallet.balance_sol
            
            # Calculate change
            change = new_balance - old_balance
            change_percent = (change / old_balance * 100) if old_balance > 0 else 0
            
            # Alert on significant changes (> 0.1 SOL or > 10%)
            if abs(change) > 0.1 or abs(change_percent) > 10:
                await self._send_balance_alert(
                    wallet=wallet,
                    old_balance=old_balance,
                    new_balance=new_balance,
                    change=change,
                    change_percent=change_percent
                )
            
            # Update database
            db_manager.update_wallet_balance(wallet.address, new_balance)
            
        except Exception as e:
            print(f"❌ Error checking wallet {wallet.address[:8]}...: {e}")
    
    async def _check_recent_transactions(self, wallet):
        """Check recent transactions for whale movements"""
        try:
            # Get recent transactions from Helius if available
            if helius_api.enabled:
                transactions = await helius_api.get_transactions(wallet.address, limit=5)
                
                for tx in transactions:
                    await self._analyze_transaction(tx, wallet)
            else:
                # Fallback to basic RPC
                transactions = solana_rpc.get_recent_transactions(wallet.address, limit=5)
                
                # Basic analysis (just log for now)
                if transactions:
                    print(f"📝 Recent tx for {wallet.address[:8]}...: {len(transactions)} found")
                    
        except Exception as e:
            print(f"❌ Error checking transactions: {e}")
    
    async def _analyze_transaction(self, tx: Dict[str, Any], wallet):
        """Analyze a single transaction for whale movements"""
        try:
            # Check for large SOL transfers
            if 'sol_transfers' in tx:
                for transfer in tx['sol_transfers']:
                    amount_sol = transfer['amount']
                    
                    # Get SOL price (simplified - in production, get from API)
                    sol_price = 100  # Placeholder
                    amount_usd = amount_sol * sol_price
                    
                    if amount_usd >= self.whale_threshold:
                        await self._send_whale_alert(
                            wallet=wallet,
                            transaction=tx,
                            transfer=transfer,
                            amount_usd=amount_usd,
                            token='SOL'
                        )
            
            # Check for large token transfers
            if 'token_transfers' in tx:
                for transfer in tx['token_transfers']:
                    # Get token price (would need to fetch)
                    # For now, just note the transfer
                    print(f"🐋 Token transfer detected: {transfer.get('amount')} {transfer.get('symbol', 'tokens')}")
                    
        except Exception as e:
            print(f"❌ Error analyzing transaction: {e}")
    
    # ========== Alert Functions ==========
    
    async def _send_balance_alert(self, wallet, old_balance, new_balance, change, change_percent):
        """Send balance change alert to user"""
        try:
            # Determine direction
            if change > 0:
                direction = "📈 Increased"
                emoji = "🟢"
            else:
                direction = "📉 Decreased"
                emoji = "🔴"
            
            # Format message
            message = (
                f"{emoji} <b>Balance Alert</b>\n\n"
                f"<b>Wallet:</b> <code>{format_address(wallet.address)}</code>\n"
                f"<b>Label:</b> {wallet.label or 'Not set'}\n\n"
                f"<b>Old Balance:</b> {old_balance:.4f} SOL\n"
                f"<b>New Balance:</b> {new_balance:.4f} SOL\n"
                f"<b>Change:</b> {direction} {abs(change):.4f} SOL ({change_percent:+.2f}%)"
            )
            
            # Send to user
            await self.application.bot.send_message(
                chat_id=wallet.telegram_id,
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Balance alert sent to {wallet.telegram_id}")
            
        except Exception as e:
            print(f"❌ Error sending balance alert: {e}")
    
    async def _send_whale_alert(self, wallet, transaction, transfer, amount_usd, token='SOL'):
        """Send whale alert to user"""
        try:
            # Format message
            if token == 'SOL':
                message = (
                    f"🐋 <b>Whale Alert!</b>\n\n"
                    f"<b>Wallet:</b> <code>{format_address(wallet.address)}</code>\n"
                    f"<b>Transaction:</b> Large SOL transfer detected\n\n"
                    f"<b>Amount:</b> {transfer['amount']:.2f} SOL\n"
                    f"<b>Value:</b> {format_usd(amount_usd)}\n"
                    f"<b>From:</b> <code>{format_address(transfer['from'])}</code>\n"
                    f"<b>To:</b> <code>{format_address(transfer['to'])}</code>\n"
                )
            else:
                message = (
                    f"🐋 <b>Whale Alert!</b>\n\n"
                    f"<b>Wallet:</b> <code>{format_address(wallet.address)}</code>\n"
                    f"<b>Transaction:</b> Large token transfer detected\n\n"
                    f"<b>Token:</b> {transfer.get('symbol', 'Unknown')}\n"
                    f"<b>Amount:</b> {transfer.get('amount', 0)}\n"
                    f"<b>From:</b> <code>{format_address(transfer.get('from', ''))}</code>\n"
                    f"<b>To:</b> <code>{format_address(transfer.get('to', ''))}</code>\n"
                )
            
            # Add transaction signature if available
            if transaction.get('signature'):
                message += f"\n<b>Signature:</b> <code>{format_address(transaction['signature'])}</code>"
            
            # Send to user
            await self.application.bot.send_message(
                chat_id=wallet.telegram_id,
                text=message,
                parse_mode='HTML'
            )
            
            print(f"✅ Whale alert sent to {wallet.telegram_id}")
            
        except Exception as e:
            print(f"❌ Error sending whale alert: {e}")
    
    # ========== Auto-Tracking Functions ==========
    
    async def _check_for_new_wallets(self, wallet, transaction):
        """Check if transaction involves new wallets that should be auto-tracked"""
        try:
            # Extract addresses from transaction
            addresses_to_check = []
            
            if 'sol_transfers' in transaction:
                for transfer in transaction['sol_transfers']:
                    if transfer['to'] and transfer['to'] != wallet.address:
                        addresses_to_check.append(transfer['to'])
            
            if 'token_transfers' in transaction:
                for transfer in transaction['token_transfers']:
                    if transfer.get('to') and transfer['to'] != wallet.address:
                        addresses_to_check.append(transfer['to'])
            
            # Check each address
            for address in addresses_to_check:
                await self._auto_track_wallet(address, wallet)
                
        except Exception as e:
            print(f"❌ Error checking for new wallets: {e}")
    
    async def _auto_track_wallet(self, new_address: str, source_wallet):
        """Automatically track a new wallet that received funds"""
        try:
            # Check if already tracked
            all_wallets = db_manager.get_all_active_wallets()
            if any(w.address == new_address for w in all_wallets):
                return
            
            # Get balance to see if it's a whale
            balance = solana_rpc.get_balance(new_address)
            
            # Only auto-track if balance > 10 SOL (whale threshold)
            if balance > 10:
                # Notify user
                message = (
                    f"🔄 <b>New Wallet Detected!</b>\n\n"
                    f"A wallet you're tracking sent funds to a new address:\n\n"
                    f"<b>New Wallet:</b> <code>{format_address(new_address)}</code>\n"
                    f"<b>Balance:</b> {balance:.4f} SOL\n\n"
                    f"Use /track {new_address} to start monitoring this wallet."
                )
                
                await self.application.bot.send_message(
                    chat_id=source_wallet.telegram_id,
                    text=message,
                    parse_mode='HTML'
                )
                
                print(f"✅ Auto-track suggestion sent for {new_address[:8]}...")
                
        except Exception as e:
            print(f"❌ Error auto-tracking wallet: {e}")