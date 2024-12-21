import requests
import logging
import time
from threading import Thread

# API and Webhook Configurations
DEXSCREENER_API_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with actual URL
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def send_discord_notification(token):
    """
    Send a Discord notification with token details.
    """
    try:
        message = (
            f"**Token Qualified!**\n"
            f"**Name**: {token['name']}\n"
            f"**Symbol**: {token['symbol']}\n"
            f"**Contract Address**: {token['address']}\n"
            f"**Market Cap**: ${token['market_cap']:,.2f}\n"
        )
        headers = {"Content-Type": "application/json"}
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers=headers)
        if response.status_code == 204:
            logging.info(f"Discord notification sent for {token['name']} ({token['symbol']})")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")


def fetch_tokens():
    """
    Fetch token data from the Dexscreener API.
    """
    try:
        headers = {"accept": "application/json"}
        response = requests.get(DEXSCREENER_API_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logging.info("Tokens fetched successfully from Dexscreener API.")
            return data.get("tokens", [])
        else:
            logging.error(f"Error fetching tokens: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error during fetch: {e}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on specified criteria.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            # Extract fields with defaults
            name = token.get("name", "Unknown")
            symbol = token.get("symbol", "Unknown")
            address = token.get("address", None)
            volume_24h = token.get("volumeUSD", 0)  # Assuming 24h volume in USD
            holders = token.get("holders", 0)
            market_cap = token.get("marketCapUSD", 0)  # Assuming market cap in USD
            liquidity = token.get("liquidityUSD", 0)  # Assuming liquidity in USD
            socials = token.get("socialLinks", {})

            # Log actual token data for debugging
            logging.debug(f"Token data: {token}")

            # Apply criteria
            if (
                volume_24h >= 1_000_000 and
                holders >= 2_000 and
                market_cap >= 2_000_000 and
                liquidity >= 600_000 and
                ("telegram" in socials or "twitter" in socials)
            ):
                logging.info(f"Token qualified: {name} ({symbol}, {address})")
                qualified_tokens.append({
                    "name": name,
                    "symbol": symbol,
                    "address": address,
                    "market_cap": market_cap,
                })
            else:
                logging.info(f"Token did not meet criteria: {name} ({symbol}, {address})")
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
        "contract_address": token["address"],
        "symbol": token["symbol"],
        "name": token["name"],
        "market_cap": token["market_cap"],
    }
    try:
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload)
        if response.status_code == 200:
            logging.info(f"✅ Successfully sent {token['name']} ({token['symbol']}) to trading bot!")
        else:
            logging.error(f"❌ Failed to send {token['name']}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending token to trading bot: {e}")


def start_fetching_tokens():
    """
    Start fetching tokens in a continuous loop.
    """
    while True:
        tokens = fetch_tokens()
        if tokens:
            qualified_tokens = filter_tokens(tokens)
            for token in qualified_tokens:
                send_discord_notification(token)
                send_to_trading_bot(token)
        time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
