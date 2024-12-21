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
            f"**Chain**: {token['chainId']}\n"
            f"**Market Cap**: ${token['marketCap']:,.2f}\n"
            f"**Liquidity**: ${token['liquidity']:,.2f}\n"
            f"**24h Volume**: ${token['volume24h']:,.2f}\n"
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
    Fetch token profiles from the Dexscreener API's search endpoint.
    """
    try:
        logging.info(f"Fetching tokens from {DEXSCREENER_SEARCH_URL}...")
        response = requests.get(DEXSCREENER_SEARCH_URL, timeout=10)
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
            # Extract relevant fields
            base = token.get("baseToken", {})
            chain_id = token.get("chainId", "")
            dex_id = token.get("dexId", "")
            name = base.get("name", "Unknown")
            symbol = base.get("symbol", "Unknown")
            address = base.get("address", None)
            market_cap = token.get("fdv", 0)  # Assuming FDV is close to market cap
            liquidity = token.get("liquidity", {}).get("usd", 0)
            volume_24h = token.get("volume", {}).get("usd", 0)

            # Log actual token data for debugging
            logging.debug(f"Token data: {token}")

            # Apply criteria
            if (
                chain_id and
                dex_id and
                volume_24h >= 1_000_000 and
                market_cap >= 2_000_000 and
                liquidity >= 600_000
            ):
                logging.info(f"Token qualified: {name} ({symbol}, {address})")
                qualified_tokens.append({
                    "name": name,
                    "symbol": symbol,
                    "address": address,
                    "chainId": chain_id,
                    "marketCap": market_cap,
                    "liquidity": liquidity,
                    "volume24h": volume_24h,
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
        "market_cap": token["marketCap"],
        "liquidity": token["liquidity"],
        "volume_24h": token["volume24h"],
    }
    try:
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info(f"✅ Successfully sent {token['name']} ({token['symbol']}) to trading bot!")
        else:
            logging.error(f"❌ Failed to send {token['name']}: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending token to trading bot: {e}")


def start_fetching_tokens():
    """
    Continuously fetch and process tokens in a background thread.
    """
    while True:
        try:
            tokens = fetch_tokens()
            if tokens:
                qualified_tokens = filter_tokens(tokens)
                for token in qualified_tokens:
                    send_discord_notification(token)
                    send_to_trading_bot(token)
        except Exception as e:
            logging.error(f"Error in token fetching loop: {e}")
        finally:
            time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    # Start the token fetching process
    Thread(target=start_fetching_tokens).start()
