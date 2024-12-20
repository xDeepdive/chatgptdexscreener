import requests
import time
import logging
from threading import Thread
import base58

# Environment Variables
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"  # Replace with your trading bot URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord Webhook URL
RUGCHECK_BASE_URL = "https://api.rugcheck.xyz/v1"  # RugCheck API URL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def is_valid_base58(token_mint):
    """
    Validate if a string is a valid Base58-encoded string.
    """
    try:
        base58.b58decode(token_mint)
        return True
    except Exception:
        return False

def send_discord_notification(message):
    """
    Send a message to Discord using a Webhook.
    """
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            logging.info(f"Discord notification sent: {message}")
        else:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

def fetch_rugcheck_report(token_address):
    """
    Fetch the RugCheck report for a given token mint address.
    """
    try:
        url = f"{RUGCHECK_BASE_URL}/tokens/{token_address}/report/summary"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to fetch RugCheck report: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error fetching RugCheck report: {e}")
        return None

def fetch_tokens():
    """
    Fetch token profiles from the DexScreener API endpoint.
    """
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        logging.info(f"Fetching tokens from {url}...")
        if response.status_code == 200:
            logging.info("Tokens fetched successfully!")
            send_discord_notification("✅ Tokens fetched successfully from DexScreener!")
            return response.json()
        else:
            error_message = f"Error fetching tokens: {response.status_code} - {response.text}"
            logging.error(error_message)
            send_discord_notification(f"❌ {error_message}")
            return []
    except Exception as e:
        error_message = f"Error during fetch: {e}"
        logging.error(error_message)
        send_discord_notification(f"❌ {error_message}")
        return []

def filter_tokens(tokens):
    """
    Filter tokens based on specific criteria.
    """
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

            # Skip invalid Base58 token mints
            if not is_valid_base58(token_address):
                logging.error(f"Invalid Base58 token mint: {token_address}")
                continue

            # Fetch RugCheck report
            rugcheck_report = fetch_rugcheck_report(token_address)
            if rugcheck_report and rugcheck_report.get("status") == "fail":
                logging.warning(f"Token failed RugCheck: {description} (Address: {token_address})")
                continue

            # Apply advanced filters
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
    """
    Send qualified tokens to the trading bot.
    """
    payload = {"contract_address": contract_address, "symbol": token_symbol}
    try:
        logging.info(f"Attempting to send to trading bot: {payload}")
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload)
        if response.status_code == 200:
            success_message = f"✅ Successfully sent {token_symbol} ({contract_address}) to trading bot!"
            logging.info(success_message)
            send_discord_notification(success_message)
        else:
            error_message = f"❌ Failed to send {token_symbol}. Response: {response.status_code} - {response.text}"
            logging.error(error_message)
            send_discord_notification(error_message)
    except Exception as e:
        error_message = f"❌ Error sending {token_symbol} to trading bot: {e}"
        logging.error(error_message)
        send_discord_notification(error_message)

def start_fetching_tokens():
    """
    Start fetching tokens in a continuous loop.
    """
    while True:
        tokens = fetch_tokens()
        if tokens:
            qualified_tokens = filter_tokens(tokens)
            for token in qualified_tokens:
                send_to_trading_bot(token["contract_address"], token["symbol"])
        time.sleep(120)  # Wait for 2 minutes before fetching tokens again

if __name__ == "__main__":
    # Start the token-fetching loop
    Thread(target=start_fetching_tokens).start()
