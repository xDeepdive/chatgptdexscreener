import requests
import time
import logging
from threading import Thread

# Environment Variables
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"
RUGCHECK_BASE_URL = "https://api.rugcheck.xyz/v1"
TWITTER_SCORE_URL = "https://twitterscore.io/api/v1/score"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_discord_notification(message):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, headers=headers)
        if response.status_code != 204:
            logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")

def fetch_tokens():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logging.info("Tokens fetched successfully!")
            send_discord_notification("✅ Tokens fetched successfully from DexScreener!")
            return response.json()
        logging.error(f"Error fetching tokens: {response.status_code} - {response.text}")
        return []
    except Exception as e:
        logging.error(f"Error during fetch: {e}")
        return []

def fetch_twitter_score(handle):
    try:
        url = f"{TWITTER_SCORE_URL}/{handle}"
        response = requests.get(url)
        if response.status_code == 200:
            score = response.json().get("score", 0)
            logging.info(f"Twitter score for @{handle}: {score}")
            return score
        logging.error(f"Failed to fetch Twitter score: {response.status_code} - {response.text}")
        return 0
    except Exception as e:
        logging.error(f"Error fetching Twitter score: {e}")
        return 0

def filter_tokens(tokens):
    qualified_tokens = []
    for token in tokens:
        try:
            contract_address = token.get("tokenAddress")
            symbol = token.get("description")
            volume_24h = token.get("volume24h", 0)
            days_old = token.get("daysOld", 0)
            holders = token.get("holders", 0)
            links = token.get("links", [])
            has_social_links = any(link.get("type") in ["twitter", "telegram", "discord"] for link in links)

            if not contract_address or not symbol:
                logging.warning(f"Skipping token with missing fields: {token}")
                continue

            if 1 <= days_old <= 400 and volume_24h >= 1_000_000 and holders <= 5_000 and has_social_links:
                twitter_handles = [link.get("handle") for link in links if link.get("type") == "twitter"]
                if twitter_handles:
                    score = fetch_twitter_score(twitter_handles[0])
                    if score < 3:  # Example threshold
                        logging.warning(f"Token {symbol} skipped due to low Twitter score: {score}")
                        continue
                qualified_tokens.append({"contract_address": contract_address, "symbol": symbol})
        except KeyError as e:
            logging.error(f"Missing key in token data: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

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
                send_to_trading_bot(token.get("contract_address"), token.get("symbol"))
        time.sleep(120)

if __name__ == "__main__":
    Thread(target=start_fetching_tokens).start()
