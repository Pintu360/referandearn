# handlers/commands.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import asyncio
from datetime import datetime

from database.crud import db_manager
from services import solana_rpc, helius_api, solscan_api, dexscreener_api
from utils.helpers import (
    validate_solana_address, format_address, format_number,
    format_usd, format_timestamp, extract_addresses, 
    get_risk_level, chunk_text
)

class CommandHandlers:
    """All Telegram command handlers"""
    
    def __init__(self, application):
        self.application = application
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register all handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("track", self.track_wallet))
        self.application.add_handler(CommandHandler("untrack", self.untrack_wallet))
        self.application.add_handler(CommandHandler("list", self.list_wallets))
        self.application.add_handler(CommandHandler("balance", self.get_balance))
        self.application.add_handler(CommandHandler("price", self.get_price))
        self.application.add_handler(CommandHandler("search", self.search_token))
        self.application.add_handler(CommandHandler("stats", self.get_stats))
        
        # Message handler for addresses
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.handle_message
        ))
        
        # Callback handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        print("✅ Command handlers registered")
    
    # ========== Command Handlers ==========
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Save user to database
        db_user = db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_message = (
            f"🚀 <b>Welcome to Solana Tracker Bot!</b>\n\n"
            f"Hello {user.first_name}! I can help you track Solana wallets "
            f"and check token prices.\n\n"
            f"<b>Quick Commands:</b>\n"
            f"• /track &lt;address&gt; - Track a wallet\n"
            f"• /list - Show your tracked wallets\n"
            f"• /balance &lt;address&gt; - Check wallet balance\n"
            f"• /price &lt;address&gt; - Check token price\n"
            f"• /search &lt;query&gt; - Search for tokens\n\n"
            f"<b>Tips:</b>\n"
            f"• Send me any Solana address for quick actions\n"
            f"• Use /help to see all commands"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='HTML')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "📚 <b>Solana Tracker Bot Commands</b>\n\n"
            
            "<b>Wallet Tracking:</b>\n"
            "/track &lt;address&gt; [label] - Track a wallet\n"
            "/untrack &lt;address&gt; - Stop tracking a wallet\n"
            "/list - Show your tracked wallets\n"
            "/balance &lt;address&gt; - Check wallet balance\n\n"
            
            "<b>Token Information:</b>\n"
            "/price &lt;address&gt; - Get token price from DexScreener\n"
            "/search &lt;query&gt; - Search for tokens by name/symbol\n\n"
            
            "<b>Other:</b>\n"
            "/stats - Bot statistics\n"
            "/help - Show this message\n\n"
            
            "<b>Features:</b>\n"
            "✅ Real-time wallet tracking\n"
            "✅ Token prices from DexScreener\n"
            "✅ Balance change notifications\n"
            "✅ No limits, completely free\n\n"
            
            "Send me any Solana address to get started!"
        )
        
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def track_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /track command"""
        user = update.effective_user
        
        # Check if address provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a wallet address.\n"
                "Example: /track <address> [label]"
            )
            return
        
        address = context.args[0]
        label = ' '.join(context.args[1:]) if len(context.args) > 1 else None
        
        # Validate address
        if not validate_solana_address(address):
            await update.message.reply_text("❌ Invalid Solana address")
            return
        
        # Get user from database
        db_user = db_manager.get_or_create_user(user.id)
        
        # Check wallet limit
        wallet_count = db_manager.get_wallet_count(db_user.id)
        if wallet_count >= 100:
            await update.message.reply_text(
                "❌ You've reached the maximum limit of 100 tracked wallets."
            )
            return
        
        try:
            # Add wallet to database
            wallet = db_manager.add_wallet(
                telegram_id=user.id,
                user_id=db_user.id,
                address=address,
                label=label
            )
            
            # Get initial balance
            balance = solana_rpc.get_balance(address)
            db_manager.update_wallet_balance(address, balance)
            
            # Success message
            message = (
                f"✅ <b>Wallet Tracked Successfully!</b>\n\n"
                f"Address: <code>{format_address(address)}</code>\n"
                f"Label: {label or 'Not set'}\n"
                f"Balance: {balance:.4f} SOL\n\n"
                f"You will receive notifications when this wallet makes large transactions."
            )
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            if "already tracked" in str(e):
                await update.message.reply_text("❌ This wallet is already being tracked")
            else:
                await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def untrack_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /untrack command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a wallet address.\n"
                "Example: /untrack <address>"
            )
            return
        
        address = context.args[0]
        user = update.effective_user
        
        if not validate_solana_address(address):
            await update.message.reply_text("❌ Invalid Solana address")
            return
        
        try:
            db_user = db_manager.get_or_create_user(user.id)
            db_manager.remove_wallet(user_id=db_user.id, address=address)
            
            await update.message.reply_text(
                f"✅ Stopped tracking wallet: <code>{format_address(address)}</code>",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def list_wallets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        user = update.effective_user
        db_user = db_manager.get_or_create_user(user.id)
        wallets = db_manager.get_user_wallets(db_user.id)
        
        if not wallets:
            await update.message.reply_text(
                "📭 You're not tracking any wallets yet.\n"
                "Use /track <address> to start tracking."
            )
            return
        
        message = "📋 <b>Your Tracked Wallets:</b>\n\n"
        
        for i, wallet in enumerate(wallets, 1):
            label = f" ({wallet.label})" if wallet.label else ""
            message += f"{i}. <code>{format_address(wallet.address)}</code>{label}\n"
            message += f"   Balance: {wallet.balance_sol:.4f} SOL\n"
            message += f"   Added: {wallet.added_at.strftime('%Y-%m-%d')}\n\n"
        
        # Split if too long
        chunks = chunk_text(message)
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode='HTML')
    
    async def get_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a wallet address.\n"
                "Example: /balance <address>"
            )
            return
        
        address = context.args[0]
        
        if not validate_solana_address(address):
            await update.message.reply_text("❌ Invalid Solana address")
            return
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        try:
            # Get balance
            balance = solana_rpc.get_balance(address)
            
            # Get recent transactions
            transactions = solana_rpc.get_recent_transactions(address, limit=5)
            
            message = (
                f"💰 <b>Wallet Balance</b>\n"
                f"<code>{address}</code>\n\n"
                f"<b>SOL Balance:</b> {balance:.4f} SOL\n\n"
            )
            
            if transactions:
                message += "<b>Recent Transactions:</b>\n"
                for tx in transactions[:3]:
                    time_ago = format_timestamp(tx['timestamp'])
                    message += f"• {time_ago}: <code>{format_address(tx['signature'])}</code>\n"
            
            # Add buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"bal_{address}"),
                    InlineKeyboardButton("➕ Track", callback_data=f"track_{address}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message, 
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def get_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a token address.\n"
                "Example: /price <token_address>"
            )
            return
        
        address = context.args[0]
        
        if not validate_solana_address(address):
            await update.message.reply_text("❌ Invalid Solana address")
            return
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        try:
            # Get price from DexScreener
            price_data = await dexscreener_api.get_token_price(address)
            
            if not price_data:
                await update.message.reply_text(
                    "❌ No price data found for this token.\n"
                    "Try searching with /search first."
                )
                return
            
            # Format message
            message = (
                f"💰 <b>Token Price</b>\n"
                f"<code>{format_address(address)}</code>\n\n"
                f"<b>Price:</b> ${price_data['price_usd']:.8f}\n"
                f"<b>Price in SOL:</b> {price_data['price_sol']:.8f} SOL\n"
                f"<b>24h Change:</b> {price_data['price_change_24h']:+.2f}%\n"
                f"<b>Liquidity:</b> {format_usd(price_data['liquidity_usd'])}\n"
                f"<b>24h Volume:</b> {format_usd(price_data['volume_24h'])}\n"
                f"<b>DEX:</b> {price_data['dex'].title()}\n\n"
                f"<a href='{price_data['url']}'>📊 View on DexScreener</a>"
            )
            
            # Add buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"price_{address}"),
                    InlineKeyboardButton("🔍 Check Token", callback_data=f"check_{address}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='HTML',
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def search_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a search term.\n"
                "Example: /search bonk"
            )
            return
        
        query = ' '.join(context.args)
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        try:
            results = await dexscreener_api.search_tokens(query)
            
            if not results:
                await update.message.reply_text(
                    f"❌ No tokens found matching '{query}'"
                )
                return
            
            message = f"🔍 <b>Search Results for '{query}':</b>\n\n"
            
            for i, token in enumerate(results[:5], 1):
                message += (
                    f"{i}. <b>{token['symbol']}</b> - {token['name']}\n"
                    f"   Price: ${token['price_usd']:.8f}\n"
                    f"   Liquidity: {format_usd(token['liquidity_usd'])}\n"
                    f"   Address: <code>{format_address(token['address'])}</code>\n\n"
                )
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def get_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        # This would be implemented with actual database stats
        stats_message = (
            "📊 <b>Bot Statistics</b>\n\n"
            "• Total Users: <i>Coming soon</i>\n"
            "• Tracked Wallets: <i>Coming soon</i>\n"
            "• Total Transactions: <i>Coming soon</i>\n"
            "• Tokens Monitored: <i>Coming soon</i>\n\n"
            "Bot uptime: 24/7 on Render 🚀"
        )
        
        await update.message.reply_text(stats_message, parse_mode='HTML')
    
    # ========== Message Handlers ==========
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        text = update.message.text.strip()
        
        # Check if message contains Solana addresses
        addresses = extract_addresses(text)
        
        if addresses:
            # Handle first address found
            address = addresses[0]
            
            keyboard = [
                [
                    InlineKeyboardButton("💰 Balance", callback_data=f"bal_{address}"),
                    InlineKeyboardButton("💵 Price", callback_data=f"price_{address}")
                ],
                [
                    InlineKeyboardButton("➕ Track", callback_data=f"track_{address}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"📝 <b>Address Detected:</b>\n"
                f"<code>{format_address(address)}</code>\n\n"
                f"What would you like to do?",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            # No address found, show help
            await update.message.reply_text(
                "Send a valid Solana address or use /help to see commands."
            )
    
    # ========== Callback Handlers ==========
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data.startswith("bal_"):
                address = data[4:]
                await self._callback_balance(query, address)
            
            elif data.startswith("price_"):
                address = data[6:]
                await self._callback_price(query, address)
            
            elif data.startswith("track_"):
                address = data[6:]
                await self._callback_track(query, address)
            
            elif data.startswith("check_"):
                address = data[6:]
                await self._callback_check(query, address)
            
            elif data == "cancel":
                await query.edit_message_text("❌ Action cancelled.")
            
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def _callback_balance(self, query, address: str):
        """Handle balance callback"""
        balance = solana_rpc.get_balance(address)
        
        message = (
            f"💰 <b>Wallet Balance</b>\n"
            f"<code>{address}</code>\n\n"
            f"<b>SOL Balance:</b> {balance:.4f} SOL"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"bal_{address}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def _callback_price(self, query, address: str):
        """Handle price callback"""
        await query.edit_message_text("🔍 Fetching price...")
        
        price_data = await dexscreener_api.get_token_price(address)
        
        if not price_data:
            await query.edit_message_text("❌ No price data found")
            return
        
        message = (
            f"💰 <b>Token Price</b>\n"
            f"<code>{format_address(address)}</code>\n\n"
            f"<b>Price:</b> ${price_data['price_usd']:.8f}\n"
            f"<b>24h Change:</b> {price_data['price_change_24h']:+.2f}%\n"
            f"<b>Liquidity:</b> {format_usd(price_data['liquidity_usd'])}"
        )
        
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"price_{address}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    async def _callback_track(self, query, address: str):
        """Handle track callback"""
        user = query.from_user
        
        try:
            db_user = db_manager.get_or_create_user(user.id)
            
            # Check wallet limit
            wallet_count = db_manager.get_wallet_count(db_user.id)
            if wallet_count >= 100:
                await query.edit_message_text("❌ Maximum wallets reached (100)")
                return
            
            # Add wallet
            wallet = db_manager.add_wallet(
                telegram_id=user.id,
                user_id=db_user.id,
                address=address
            )
            
            # Get initial balance
            balance = solana_rpc.get_balance(address)
            db_manager.update_wallet_balance(address, balance)
            
            await query.edit_message_text(
                f"✅ <b>Wallet Tracked!</b>\n\n"
                f"Address: <code>{format_address(address)}</code>\n"
                f"Balance: {balance:.4f} SOL",
                parse_mode='HTML'
            )
            
        except Exception as e:
            if "already tracked" in str(e):
                await query.edit_message_text("❌ Wallet already tracked")
            else:
                await query.edit_message_text(f"❌ Error: {str(e)}")
    
    async def _callback_check(self, query, address: str):
        """Handle check token callback"""
        await query.edit_message_text("🔍 Analyzing token...")
        
        price_data = await dexscreener_api.get_token_price(address)
        
        if not price_data:
            await query.edit_message_text("❌ No data found for this token")
            return
        
        message = (
            f"🔍 <b>Token Analysis</b>\n"
            f"<code>{format_address(address)}</code>\n\n"
            f"<b>Symbol:</b> {price_data['base_token'].get('symbol', 'Unknown')}\n"
            f"<b>Name:</b> {price_data['base_token'].get('name', 'Unknown')}\n"
            f"<b>Price:</b> ${price_data['price_usd']:.8f}\n"
            f"<b>Liquidity:</b> {format_usd(price_data['liquidity_usd'])}\n"
            f"<b>24h Volume:</b> {format_usd(price_data['volume_24h'])}\n"
            f"<b>DEX:</b> {price_data['dex'].title()}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Price", callback_data=f"price_{address}"),
                InlineKeyboardButton("➕ Track", callback_data=f"track_{address}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )