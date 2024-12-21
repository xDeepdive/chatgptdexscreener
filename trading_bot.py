import requests
import logging
import time
from threading import Thread

# API and Webhook Configurations
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"

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
            f"**Liquidity**: ${token['liquidity']:,.2f}\n"
            f"**Price (USD)**: ${token['price_usd']}\n"
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
        response = requests.get(DEXSCREENER_API_URL)
        if response.status_code == 200:
            data = response.json()
            logging.info("Tokens fetched successfully from Dexscreener API.")
            return data.get("pairs", [])
        else:
            logging.error(f"Error fetching tokens: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error during fetch: {e}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on old code criteria:
    - Minimum 24-hour volume: $1,000,000
    - Minimum holders: 2,000
    - Minimum market cap: $2,000,000
    - Minimum liquidity: $600,000
    - At least one social media link (Twitter or Telegram)
    """
    qualified_tokens = []
    for token in tokens:
        try:
            base_token = token.get("baseToken", {})
            name = base_token.get("name", "Unknown")
            symbol = base_token.get("symbol", "Unknown")
            address = base_token.get("address", None)
            price_usd = float(token.get("priceUsd", 0))
            liquidity = token.get("liquidity", {}).get("usd", 0)
            market_cap = token.get("marketCap", 0)
            socials = token.get("info", {}).get("socials", [])

            # Check for social media links
            has_social = any(social.get("platform") in ["twitter", "telegram"] for social in socials)

            # Apply old code criteria
            if (
                price_usd > 0 and
                liquidity >= 600_000 and
                market_cap >= 2_000_000 and
                has_social
            ):
                logging.info(f"Token qualified: {name} ({symbol}, {address})")
                qualified_tokens.append({
                    "name": name,
                    "symbol": symbol,
                    "address": address,
                    "price_usd": price_usd,
                    "liquidity": liquidity,
                    "market_cap": market_cap,
                })
            else:
                logging.info(f"Token did not meet criteria: {name} ({symbol}, {address})")
        except Exception as e:
            logging.error(f"Error processing token: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
    return qualified_tokens


def send_to_trading_bot(contract_address, token_symbol):
    """
    Placeholder function to send qualified tokens to the trading bot.
    """
    payload = {"contract_address": contract_address, "symbol": token_symbol}
    logging.info(f"Payload for trading bot: {payload}")


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
                send_to_trading_bot(token["address"], token["symbol"])
        time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
