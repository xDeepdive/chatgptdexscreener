import requests
import time
import logging
from threading import Thread

# Environment Variables
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"  # Replace with the trading bot URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord Webhook URL
RUGCHECK_BASE_URL = "https://api.rugcheck.xyz/v1"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_discord_notification(message):
    """
    Send a message to Discord using a Webhook.
    """
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers=headers)
        if response.status_code == 204:
            logging.info(f"Discord notification sent: {message}")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

def fetch_tokens():
    """
    Fetch token profiles from the DexScreener API endpoint.
    """
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logging.info("Tokens fetched successfully!")
            send_discord_notification("✅ Tokens fetched successfully from DexScreener!")
            return response.json()
        else:
            logging.error(f"Error fetching tokens: {response.status_code} - {response.text}")
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
            contract_address = token.get("tokenAddress", None)
            symbol = token.get("description", None)
            volume_24h = token.get("volume24h", 0)
            days_old = token.get("daysOld", 0)
            holders = token.get("holders", 0)
            links = token.get("links", [])
            has_social_links = any(link.get("type") in ["twitter", "telegram", "discord"] for link in links)

            if not contract_address or not symbol:
                logging.warning(f"Skipping token with missing fields: {token}")
                continue

            # Apply additional filters
            if (
                volume_24h >= 1_000_000 and
                days_old >= 1 and
                holders <= 5000 and
                has_social_links
            ):
                logging.info(f"Token qualified: {symbol} (Address: {contract_address})")
                qualified_tokens.append({
                    "contract_address": contract_address,
                    "symbol": symbol
                })
        except KeyError as e:
            logging.error(f"Missing key in token data: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
        send_discord_notification("⚠️ No tokens qualified based on the criteria.")
    return qualified_tokens

def send_to_trading_bot(contract_address, token_symbol):
    """
    Send qualified tokens to the trading bot.
    """
    payload = {"contract_address": contract_address, "symbol": token_symbol}
    try:
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload)
        if response.status_code == 200:
            logging.info(f"✅ Successfully sent {token_symbol} ({contract_address}) to trading bot!")
        else:
            logging.error(f"❌ Failed to send {token_symbol}: {response.status_code} - {response.text}")
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
                send_to_trading_bot(token.get("contract_address"), token.get("symbol"))
        time.sleep(120)

if __name__ == "__main__":
    # Start the token-fetching loop
    Thread(target=start_fetching_tokens).start()
