import requests
import time
import logging
from threading import Thread
import base58

# Environment Variables
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"  # Replace with the trading bot URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your-webhook-url"  # Replace with your Discord Webhook URL
RUGCHECK_BASE_URL = "https://api.rugcheck.xyz/v1"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def is_valid_base58(token_mint):
    try:
        base58.b58decode(token_mint)
        return True
    except Exception:
        return False

def send_discord_notification(message):
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            logging.info(f"Discord notification sent: {message}")
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logging.warning(f"Rate-limited by Discord. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            send_discord_notification(message)
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

def fetch_tokens():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        logging.info(f"Fetching tokens from {url}...")
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
    qualified_tokens = []
    for token in tokens:
        try:
            chain_id = token.get("chainId", "")
            description = token.get("description", "")
            token_address = token.get("tokenAddress", "")
            volume_24h = token.get("volume24h", 0)
            days_old = token.get("daysOld", 0)
            holders = token.get("holders", 0)
            links = token.get("links", [])
            has_social_links = any(link.get("type") in ["twitter", "telegram", "discord"] for link in links)

            if not is_valid_base58(token_address):
                logging.error(f"Invalid Base58 token mint: {token_address}")
                continue

            if (
                chain_id == "solana" and
                volume_24h >= 1_000_000 and
                days_old >= 1 and
                holders <= 100_000 and
                has_social_links
            ):
                logging.info(f"Token qualified: {description} (Address: {token_address})")
                qualified_tokens.append({
                    "contract_address": token_address,
                    "symbol": description
                })
        except KeyError as e:
            logging.error(f"Missing key in token data: {e}")

    if not qualified_tokens:
        logging.warning("No tokens qualified based on the criteria.")
        send_discord_notification("⚠️ No tokens qualified based on the criteria.")
    return qualified_tokens

def send_to_trading_bot(contract_address, token_symbol):
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
    while True:
        tokens = fetch_tokens()
        if tokens:
            qualified_tokens = filter_tokens(tokens)
            for token in qualified_tokens:
                send_to_trading_bot(token["contract_address"], token["symbol"])
        time.sleep(120)

if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
