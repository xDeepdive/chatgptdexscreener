import requests
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
import logging

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord webhook URL
POLL_INTERVAL = 60  # Polling interval in seconds

# Filters for new tokens
TOKEN_CRITERIA = {
    "min_liquidity_usd": 600000,  # Minimum liquidity in USD
    "chain": "solana",  # Specify Solana blockchain
}

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to fetch tokens from Dexscreener API
def fetch_new_tokens():
    try:
        logging.info("Fetching tokens from Dexscreener...")
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        tokens = response.json().get("pairs", [])
        logging.info(f"Fetched {len(tokens)} tokens.")
        return tokens
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []

# Function to filter tokens based on criteria
def filter_tokens(tokens):
    filtered_tokens = []
    for token in tokens:
        try:
            # Validate structure
            liquidity = token.get("liquidity", {}).get("usd", 0)
            chain = token.get("baseToken", {}).get("chainId", "").lower()
            if liquidity >= TOKEN_CRITERIA["min_liquidity_usd"] and chain == TOKEN_CRITERIA["chain"]:
                filtered_tokens.append(token)
        except KeyError as e:
            logging.error(f"Key error when filtering token: {e}")
            continue
    logging.info(f"Filtered {len(filtered_tokens)} tokens matching criteria.")
    return filtered_tokens

# Function to send a Discord notification
def send_discord_notification(token):
    try:
        logging.info(f"Sending notification for token: {token['baseToken']['symbol']}")
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
        response = webhook.execute()
        if response.status_code == 204:
            logging.info("Notification sent successfully.")
        else:
            logging.warning(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

# Main loop
def run_bot():
    logging.info("Starting bot for Solana tokens...")
    while True:
        tokens = fetch_new_tokens()
        if tokens:
            filtered_tokens = filter_tokens(tokens)
            for token in filtered_tokens:
                send_discord_notification(token)
        else:
            logging.warning("No tokens fetched or an error occurred.")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_bot()
