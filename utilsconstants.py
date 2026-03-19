# utils/constants.py
"""
Constants used throughout the bot
"""

# Telegram message limits
TELEGRAM_MAX_MESSAGE_LENGTH = 4096

# Solana constants
LAMPORTS_PER_SOL = 1_000_000_000
SOL_DECIMALS = 9

# Known program IDs
PROGRAM_IDS = {
    'token': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',
    'associated_token': 'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
    'system': '11111111111111111111111111111111',
    'vote': 'Vote111111111111111111111111111111111111111',
    'stake': 'Stake11111111111111111111111111111111111111',
}

# Default RPC endpoints
DEFAULT_RPC_ENDPOINTS = [
    'https://api.mainnet-beta.solana.com',
    'https://solana-api.projectserum.com',
    'https://rpc.ankr.com/solana',
]

# Command descriptions for Telegram
COMMAND_DESCRIPTIONS = {
    'start': '🚀 Start the bot',
    'help': '📚 Show help message',
    'track': '📝 Track a wallet address',
    'untrack': '❌ Stop tracking a wallet',
    'list': '📋 List your tracked wallets',
    'balance': '💰 Check wallet balance',
    'price': '💵 Check token price',
    'search': '🔍 Search for tokens',
    'stats': '📊 Bot statistics',
}

# Error messages
ERROR_MESSAGES = {
    'invalid_address': '❌ Invalid Solana address',
    'not_found': '❌ Information not found',
    'api_error': '❌ API error, please try again',
    'rate_limit': '⏳ Rate limited, please wait',
    'max_wallets': '❌ Maximum wallets reached (100)',
    'already_tracking': '❌ Already tracking this wallet',
    'not_tracking': '❌ You are not tracking this wallet',
}

# Success messages
SUCCESS_MESSAGES = {
    'wallet_tracked': '✅ Wallet added to tracking',
    'wallet_untracked': '✅ Wallet removed from tracking',
    'alert_set': '✅ Alert set successfully',
}

# Button labels
BUTTON_LABELS = {
    'refresh': '🔄 Refresh',
    'back': '◀️ Back',
    'cancel': '❌ Cancel',
    'track': '➕ Track',
    'balance': '💰 Balance',
    'price': '💵 Price',
    'holders': '📊 Holders',
    'transactions': '📜 Transactions',
}

# Risk thresholds
WHALE_THRESHOLD_USD = 100_000  # $100k USD
LARGE_TX_THRESHOLD_SOL = 1_000  # 1000 SOL
LIQUIDITY_THRESHOLD_LOW = 100_000  # $100k
LIQUIDITY_THRESHOLD_MEDIUM = 500_000  # $500k

# Cache TTLs (in seconds)
CACHE_TTL = {
    'price': 60,  # 1 minute
    'balance': 30,  # 30 seconds
    'token_info': 300,  # 5 minutes
    'holders': 600,  # 10 minutes
}