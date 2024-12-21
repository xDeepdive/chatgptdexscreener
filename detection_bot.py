import requests
import time
import logging
from threading import Thread

# Environment Variables
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your-webhook-url"
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


def fetch_rugcheck_report(token_address):
    """
    Fetch the RugCheck report for a given Solana token.
    """
    try:
        url = f"{RUGCHECK_BASE_URL}/tokens/{token_address}/report/summary"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Failed to fetch RugCheck report: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error fetching RugCheck report: {e}")
        return None


def fetch_twitter_score(handle):
    """
    Fetch the Twitter score for a given Twitter handle.
    """
    try:
        url = f"{TWITTER_SCORE_URL}/{handle}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("score", 0)
        else:
            logging.warning(f"Failed to fetch Twitter score: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        logging.error(f"Error fetching Twitter score: {e}")
        return 0


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
    Filter tokens for the Solana chain based on specific criteria.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            chain_id = token.get("chainId", "")
            contract_address = token.get("tokenAddress", None)
            symbol = token.get("description", "Unknown")
            volume_24h = token.get("volume24h", 0)
            days_old = token.get("daysOld", 0)
            holders = token.get("holders", 0)
            links = token.get("links", [])
            has_social_links = any(link.get("type") in ["twitter", "telegram", "discord"] for link in links)

            # Process Solana tokens only
            if chain_id != "solana":
                logging.warning(f"Skipping non-Solana token: {chain_id}")
                continue

            # Skip tokens with missing critical fields
            if not contract_address or symbol == "Unknown":
                logging.warning(f"Skipping token due to missing critical fields: {token}")
                continue

            # Fetch RugCheck report
            rugcheck = fetch_rugcheck_report(contract_address)
            if rugcheck and rugcheck.get("status") == "fail":
                logging.warning(f"Token failed RugCheck: {symbol} (Address: {contract_address})")
                continue

            # Fetch Twitter Score if a Twitter handle is available
            twitter_handle = next((link["url"] for link in links if link.get("type") == "twitter"), None)
            twitter_score = fetch_twitter_score(twitter_handle) if twitter_handle else 0
            if twitter_score < 3:  # Minimum Twitter score
                logging.warning(f"Token {symbol} failed Twitter score check: {twitter_score}")
                continue

            # Apply filters
            if (
                1 <= days_old <= 400 and  # Days must be between 1 and 400
                volume_24h >= 1_000_000 and
                holders >= 5_000 and  # Minimum holders
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
        time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    # Start the token-fetching loop
    Thread(target=start_fetching_tokens).start()
