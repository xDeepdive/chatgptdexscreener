import requests
import logging
import time
from threading import Thread

# Configuration
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/tokens/"

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def send_discord_notification(token):
    """
    Sends a detailed Discord notification for a qualified token.
    """
    try:
        message = (
            f"**Token Qualified!**\n"
            f"**Name**: {token['name']}\n"
            f"**Symbol**: {token['symbol']}\n"
            f"**Contract Address**: {token['contract_address']}\n"
            f"**Market Cap**: ${token['market_cap']:,.2f}\n"
            f"**Chain ID**: {token['chain_id']}\n"
            f"**Price**: ${token['price_usd']:,.6f}\n"
            f"**Boosts**: {token['boosts']}\n"
            f"**Social Links**: {', '.join([link['platform'] for link in token['social_links']])}"
        )
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers={"Content-Type": "application/json"})
        if response.status_code == 204:
            logging.info(f"Discord notification sent for {token['name']} ({token['symbol']}).")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")


def fetch_tokens():
    """
    Fetch tokens data from the DexScreener API.
    """
    try:
        logging.info(f"Fetching tokens from {DEXSCREENER_API_URL}...")
        response = requests.get(DEXSCREENER_API_URL, timeout=10)
        if response.status_code == 200:
            logging.info("Tokens fetched successfully from DexScreener API.")
            return response.json().get("pairs", [])
        else:
            logging.error(f"Error fetching tokens: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logging.error(f"Error during fetch: {e}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on enhanced criteria.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            chain_id = token.get("chainId", "").lower()
            market_cap = token.get("marketCap", 0)
            volume_24h = token.get("volumeUsd", 0)
            liquidity_usd = token.get("liquidity", {}).get("usd", 0)
            boosts = token.get("boosts", {}).get("active", 0)
            social_links = token.get("info", {}).get("socials", [])
            price_usd = float(token.get("priceUsd", 0))
            pair_created_at = token.get("pairCreatedAt", 0)

            # Check for at least one valid social link
            has_social_link = any(social.get("platform") in ["telegram", "twitter", "website"] for social in social_links)

            # Filter criteria
            if (
                chain_id in ["ethereum", "bsc", "solana", "polygon"] and
                market_cap >= 2_000_000 and
                volume_24h >= 1_000_000 and
                liquidity_usd >= 600_000 and
                has_social_link and
                price_usd > 0.001 and price_usd < 100 and
                (boosts > 0 or pair_created_at > (time.time() - 30 * 86400))  # Optional new token logic
            ):
                qualified_tokens.append({
                    "name": token.get("baseToken", {}).get("name", "Unknown"),
                    "symbol": token.get("baseToken", {}).get("symbol", "Unknown"),
                    "contract_address": token.get("baseToken", {}).get("address", "Unknown"),
                    "market_cap": market_cap,
                    "chain_id": chain_id,
                    "price_usd": price_usd,
                    "boosts": boosts,
                    "social_links": social_links,
                })
        except Exception as e:
            logging.error(f"Error processing token: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
    return qualified_tokens


def send_to_trading_bot(token):
    """
    Sends the qualified token to the trading bot.
    """
    payload = {
        "contract_address": token["contract_address"],
        "symbol": token["symbol"],
        "name": token["name"],
        "market_cap": token["market_cap"],
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
        tokens = fetch_tokens()
        if tokens:
            qualified_tokens = filter_tokens(tokens)
            for token in qualified_tokens:
                send_discord_notification(token)
                send_to_trading_bot(token)
        time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
