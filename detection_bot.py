import requests
import logging
import time
from threading import Thread

# API and Webhook Configurations
DEXSCREENER_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Dynamic Queries List
QUERIES = ["usdt", "btc", "eth", "sol", "doge", "bnb"]  # Add or modify as needed


def send_discord_notification(token):
    """
    Send a Discord notification with token details.
    """
    try:
        message = (
            f"**Token Qualified!**\n"
            f"**Name**: {token['baseToken']['name']}\n"
            f"**Symbol**: {token['baseToken']['symbol']}\n"
            f"**Contract Address**: {token['baseToken']['address']}\n"
            f"**Market Cap**: ${token['marketCap']:,.2f}\n"
        )
        headers = {"Content-Type": "application/json"}
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers=headers)
        if response.status_code == 204:
            logging.info(f"Discord notification sent for {token['baseToken']['name']} ({token['baseToken']['symbol']})")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")


def fetch_tokens(query):
    """
    Fetch token profiles from the Dexscreener API's search endpoint using a dynamic query.
    """
    try:
        logging.info(f"Fetching tokens from {DEXSCREENER_SEARCH_URL} with query: {query}...")
        response = requests.get(f"{DEXSCREENER_SEARCH_URL}?q={query}", timeout=10)
        if response.status_code == 200:
            logging.info("Tokens fetched successfully!")
            return response.json().get("pairs", [])
        else:
            error_message = f"Error fetching tokens: {response.status_code} - {response.text}"
            logging.error(error_message)
            return []
    except Exception as e:
        logging.error(f"Error during fetch: {e}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on specific criteria.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            liquidity = token.get("liquidity", {}).get("usd", 0)
            market_cap = token.get("marketCap", 0)
            base_token = token.get("baseToken", {})
            social_links = token.get("info", {}).get("socials", [])

            has_socials = any(social.get("platform") in ["twitter", "telegram"] for social in social_links)
            if liquidity >= 600_000 and market_cap >= 2_000_000 and has_socials:
                logging.info(f"Token qualified: {base_token.get('name')} ({base_token.get('symbol')})")
                qualified_tokens.append(token)
            else:
                logging.info(f"Token did not meet criteria: {base_token.get('name')} ({base_token.get('symbol')})")
        except Exception as e:
            logging.error(f"Error processing token: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
    return qualified_tokens


def send_to_trading_bot(token):
    """
    Send qualified tokens to the trading bot.
    """
    payload = {
        "contract_address": token["baseToken"]["address"],
        "symbol": token["baseToken"]["symbol"],
        "name": token["baseToken"]["name"],
        "market_cap": token["marketCap"],
    }
    try:
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info(f"✅ Successfully sent {token['baseToken']['name']} to trading bot!")
        else:
            logging.error(f"❌ Failed to send {token['baseToken']['name']} to trading bot: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending token to trading bot: {e}")


def start_fetching_tokens():
    """
    Continuously fetch and process tokens for each query in the dynamic query list.
    """
    while True:
        for query in QUERIES:
            try:
                tokens = fetch_tokens(query)
                if tokens:
                    qualified_tokens = filter_tokens(tokens)
                    for token in qualified_tokens:
                        send_discord_notification(token)
                        send_to_trading_bot(token)
            except Exception as e:
                logging.error(f"Error in token processing loop: {e}")
            time.sleep(60)  # Wait 1 minute between each query


if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
