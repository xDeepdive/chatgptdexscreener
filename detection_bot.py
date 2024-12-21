import requests
import logging
import time
from threading import Thread

# API Configuration
BIRDEYE_API_URL = "https://public-api.birdeye.so/defi/tokenlist"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord Webhook URL
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"
API_KEY = "f4d2fe2722064dd2a912cab4da66fa1c"  # Replace with your API key

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_discord_notification(token_details):
    """
    Send a detailed notification to Discord via a webhook.
    """
    try:
        headers = {"Content-Type": "application/json"}
        message = (
            f"**Token Qualified:**\n"
            f"**Name:** {token_details['name']}\n"
            f"**Symbol:** {token_details['symbol']}\n"
            f"**Contract Address:** {token_details['address']}\n"
            f"**Market Cap:** ${token_details['market_cap']:,}\n"
        )
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers=headers)
        if response.status_code == 204:
            logging.info(f"Discord notification sent: {token_details['name']} ({token_details['symbol']})")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

def fetch_tokens():
    """
    Fetch token data from the BirdEye API.
    """
    try:
        params = {
            "sort_by": "v24hUSD",
            "sort_type": "desc",
            "offset": 0,
            "limit": 50,
            "min_liquidity": 600000,
        }
        headers = {
            "accept": "application/json",
            "X-API-KEY": API_KEY,
            "x-chain": "solana",
        }
        response = requests.get(BIRDEYE_API_URL, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logging.info("Tokens fetched successfully!")
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
            name = token.get("name", "Unknown")
            symbol = token.get("symbol", "Unknown")
            address = token.get("address", None)
            market_cap = token.get("market_cap", 0)
            liquidity = token.get("liquidity", 0)
            socials = token.get("socials", {})

            # Apply filters
            if (
                liquidity >= 600000 and  # Minimum liquidity of 600k
                market_cap > 0 and       # Ensure market cap exists
                "telegram" in socials or "twitter" in socials  # At least one social presence
            ):
                logging.info(f"Token qualified: {name} ({symbol}, {address})")
                qualified_token = {
                    "name": name,
                    "symbol": symbol,
                    "address": address,
                    "market_cap": market_cap,
                }
                qualified_tokens.append(qualified_token)
                send_discord_notification(qualified_token)  # Send Discord notification
            else:
                logging.info(f"Token did not meet criteria: {name} ({symbol}, {address})")
        except Exception as e:
            logging.error(f"Error processing token: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
        send_discord_notification({"name": "None", "symbol": "None", "address": "None", "market_cap": 0})
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
                send_to_trading_bot(token)
        time.sleep(300)  # Fetch every 5 minutes

if __name__ == "__main__":
    # Start the token-fetching loop
    Thread(target=start_fetching_tokens).start()
