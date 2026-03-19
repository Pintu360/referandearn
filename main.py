#!/usr/bin/env python3
"""
Solana Tracker Bot - Main Entry Point
Complete Telegram bot for tracking Solana wallets and tokens
"""

import os
import sys
import logging
import asyncio
import threading
import signal
from datetime import datetime

from telegram.ext import ApplicationBuilder
from flask import Flask

# Local imports
from config import config
from database.crud import db_manager
from handlers.commands import CommandHandlers
from handlers.tasks import BackgroundTasks
from wsgi import app as flask_app

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

class SolanaTrackerBot:
    """Main bot class"""
    
    def __init__(self):
        """Initialize the bot"""
        logger.info("🚀 Initializing Solana Tracker Bot...")
        
        # Validate configuration
        self._validate_config()
        
        # Initialize Telegram application
        self.application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize background tasks
        self.background_tasks = BackgroundTasks(self.application)
        
        # Setup handlers
        self.command_handlers = CommandHandlers(self.application)
        
        # Bot status
        self.start_time = datetime.utcnow()
        self.is_running = False
        
        logger.info("✅ Bot initialized successfully")
    
    def _validate_config(self):
        """Validate required configuration"""
        try:
            config.validate()
            logger.info("✅ Configuration validated")
        except ValueError as e:
            logger.error(f"❌ Configuration error: {e}")
            sys.exit(1)
    
    async def post_init(self):
        """Run after bot initialization"""
        logger.info("🚀 Bot is starting up...")
        self.is_running = True
        
        # Test database connection
        try:
            session = db_manager.get_session()
            session.execute("SELECT 1")
            session.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
        
        # Start background tasks
        logger.info("🔄 Starting background tasks...")
        await self.background_tasks.start()
        
        # Set bot commands in Telegram
        await self._set_bot_commands()
        
        logger.info("✅ Bot is ready!")
    
    async def post_shutdown(self):
        """Run before bot shutdown"""
        logger.info("🛑 Bot is shutting down...")
        self.is_running = False
        
        # Stop background tasks
        await self.background_tasks.stop()
        
        logger.info("✅ Bot shutdown complete")
    
    async def _set_bot_commands(self):
        """Set bot commands in Telegram menu"""
        commands = [
            ("start", "🚀 Start the bot"),
            ("help", "📚 Show help"),
            ("track", "📝 Track a wallet"),
            ("untrack", "❌ Stop tracking"),
            ("list", "📋 Your wallets"),
            ("balance", "💰 Check balance"),
            ("price", "💵 Token price"),
            ("search", "🔍 Search tokens"),
            ("stats", "📊 Bot stats")
        ]
        
        try:
            await self.application.bot.set_my_commands(commands)
            logger.info("✅ Bot commands set")
        except Exception as e:
            logger.error(f"❌ Failed to set commands: {e}")
    
    def run(self):
        """Run the bot"""
        try:
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Add post init handler
            self.application.post_init = self.post_init
            self.application.post_shutdown = self.post_shutdown
            
            # Start the bot
            logger.info("▶️ Starting bot polling...")
            self.application.run_polling()
            
        except KeyboardInterrupt:
            logger.info("⏸️ Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Bot crashed: {e}")
            raise
        finally:
            # Ensure cleanup
            asyncio.run(self.post_shutdown())
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)

# ========== Flask Health Check Server ==========

def run_flask():
    """Run Flask server for health checks (required by Render)"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"📡 Starting health check server on port {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== Main Entry Point ==========

def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Solana Tracker Bot Starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Environment: {'production' if os.environ.get('RENDER') else 'development'}")
    logger.info("=" * 50)
    
    # Start Flask in a separate thread for Render health checks
    if os.environ.get('RENDER'):
        logger.info("📡 Render environment detected, starting health check server")
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
    
    # Create and run bot
    bot = SolanaTrackerBot()
    bot.run()

if __name__ == "__main__":
    main()