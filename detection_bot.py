import requests
import time
from discord_webhook import DiscordWebhook, DiscordEmbed

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord webhook URL
POLL_INTERVAL = 60  # Polling interval in seconds

# Filters for new tokens (customize as needed)
TOKEN_CRITERIA = {
    "min_liquidity_usd": 600000,  # Minimum liquidity in USD
    "chain": "solana",  # Specify Solana blockchain
}

# Function to fetch tokens from Dexscreener API
def fetch_new_tokens():
    try:
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        tokens = response.json().get("pairs", [])
        return tokens
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

# Function to filter tokens based on criteria
def filter_tokens(tokens):
    filtered_tokens = []
    for token in tokens:
        try:
            liquidity = token["liquidity"]["usd"]
            chain = token["baseToken"]["chainId"]
            if liquidity >= TOKEN_CRITERIA["min_liquidity_usd"] and chain == TOKEN_CRITERIA["chain"]:
                filtered_tokens.append(token)
        except KeyError:
            continue
    return filtered_tokens

# Function to send a Discord notification
def send_discord_notification(token):
    try:
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(
            title=f"New Token Alert: {token['baseToken']['name']}",
            description=f"**Symbol**: {token['baseToken']['symbol']}\n"
                        f"**Liquidity (USD)**: {token['liquidity']['usd']}\n"
                        f"**Chain**: {token['baseToken']['chainId']}\n"
                        f"[View on Dexscreener]({token['url']})",
            color=0x00ff00,
        )
        webhook.add_embed(embed)
        webhook.execute()
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

# Main loop
def run_bot():
    print("Starting bot for Solana...")
    while True:
        tokens = fetch_new_tokens()
        filtered_tokens = filter_tokens(tokens)
        for token in filtered_tokens:
            send_discord_notification(token)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_bot()
