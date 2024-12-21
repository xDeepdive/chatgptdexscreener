import requests
import logging
import time
from threading import Thread

# API Configuration
BIRDEYE_TOKENLIST_API_URL = "https://public-api.birdeye.so/defi/tokenlist"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"
API_KEY = "f4d2fe2722064dd2a912cab4da66fa1c"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_discord_notification(message):
    """
    Send a notification to Discord via a webhook.
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
    Fetch token data from the BirdEye Token List API.
    """
    try:
        params = {
            "sort_by": "v24hUSD",
            "sort_type": "desc",
            "min_liquidity": 100,  # Minimum liquidity in USD
            "offset": 0,
            "limit": 50,
        }
        headers = {
            "accept": "application/json",
            "X-API-KEY": API_KEY,
            "x-chain": "solana",
        }
        response = requests.get(BIRDEYE_TOKENLIST_API_URL, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logging.info("Tokens fetched successfully!")
            send_discord_notification("✅ Tokens fetched successfully from BirdEye Token List API!")
            return data.get("data", {}).get("tokens", [])
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
            address = token.get("address")
            liquidity = token.get("liquidity", 0)
            last_trade_unix_time = token.get("lastTradeUnixTime", 0)

            # Apply filters
            if liquidity > 100000:  # Minimum liquidity in USD
                logging.info(f"Token qualified: {address}")
                qualified_tokens.append({
                    "address": address,
                    "liquidity": liquidity,
                    "last_trade_unix_time": last_trade_unix_time,
                })
            else:
                logging.info(f"Token did not meet criteria: {address}")
        except Exception as e:
            logging.error(f"Error processing token: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
        send_discord_notification("⚠️ No tokens qualified based on the criteria.")
    return qualified_tokens

def send_to_trading_bot(token):
    """
    Send qualified tokens to the trading bot.
    """
    payload = {
        "contract_address": token["address"],
        "liquidity": token["liquidity"],
        "last_trade_unix_time": token["last_trade_unix_time"],
    }
    try:
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload)
        if response.status_code == 200:
            logging.info(f"✅ Successfully sent token {token['address']} to trading bot!")
        else:
            logging.error(f"❌ Failed to send token {token['address']}: {response.status_code} - {response.text}")
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
                send_to_trading_bot(token)
        time.sleep(300)  # Fetch every 5 minutes

if __name__ == "__main__":
    # Start the token-fetching loop
    Thread(target=start_fetching_tokens).start()
