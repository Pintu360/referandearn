# Solana Tracker Bot 🤖

A comprehensive Telegram bot for tracking Solana wallets, monitoring transactions, and checking token prices.

## Features ✨

- **Wallet Tracking**: Monitor any Solana wallet for balance changes
- **Price Checks**: Real-time token prices from DexScreener
- **Whale Alerts**: Get notified of large transactions (>$100k)
- **Auto-tracking**: Automatically detect new wallets from transactions
- **Token Search**: Search for tokens by name or symbol
- **No Limits**: Completely free with unlimited wallets

## Commands 📚

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/track <address>` | Track a wallet |
| `/untrack <address>` | Stop tracking |
| `/list` | Show your wallets |
| `/balance <address>` | Check balance |
| `/price <address>` | Token price |
| `/search <query>` | Search tokens |
| `/stats` | Bot statistics |

## Quick Start 🚀

1. **Send any Solana address** to the bot
2. Click "Track" to start monitoring
3. Get notified of balance changes
4. Use `/price` to check token prices

## Deployment on Render

This bot is designed to run on Render.com:

1. Fork this repository
2. Create a new Web Service on Render
3. Connect your repository
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `DATABASE_URL` (from Render PostgreSQL)
5. Deploy!

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql://...
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
HELIUS_API_KEY=your_key_here (optional)
SOLSCAN_API_KEY=your_key_here (optional)
CHECK_INTERVAL=60
MAX_WALLETS_PER_USER=100
PORT=10000