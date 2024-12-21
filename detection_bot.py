import os
import requests
import time
from flask import Flask, jsonify
from discord_webhook import DiscordWebhook, DiscordEmbed
import logging

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/pairs"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Replace with your Discord webhook URL
POLL_INTERVAL = 60  # Polling interval in seconds

# Criteria for filtering tokens
TOKEN_CRITERIA = {
    "min_liquidity_usd": 600000,  # Minimum liquidity in USD
    "chain": "solana",  # Target blockchain
}

# Flask app initialization
app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_tokens():
    """
    Fetch the latest token data from Dexscreener.
    """
    try:
        logging.info("Fetching tokens from Dexscreener...")
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        tokens = response.json().get("pairs", [])
        logging.info(f"Fetched {len(tokens)} tokens.")
        return tokens
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on liquidity and chain criteria.
    """
    filtered_tokens = []
    for token in tokens:
        try:
            liquidity = token.get("liquidity", {}).get("usd", 0)
            chain = token.get("baseToken", {}).get("chainId", "").lower()
            if liquidity >= TOKEN_CRITERIA["min_liquidity_usd"] and chain == TOKEN_CRITERIA["chain"]:
                filtered_tokens.append(token)
        except KeyError as e:
            logging.error(f"Key error during token filtering: {e}")
            continue
    logging.info(f"{len(filtered_tokens)} tokens match the criteria.")
    return filtered_tokens


def send_discord_notification(token):
    """
    Send a Discord notification for a token.
    """
    try:
        logging.info(f"Sending Discord notification for token: {token['baseToken']['symbol']}")
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(
            title=f"New Token Alert: {token['baseToken']['name']}",
            description=f"**Symbol**: {token['baseToken']['symbol']}\n"
                        f"**Liquidity (USD)**: {token['liquidity']['usd']}\n"
                        f"**Chain**: {token['baseToken']['chainId']}\n"
                        f"[View on Dexscreener]({token['url']})",
            color=0x00ff00,
        )
        webhook.add_embed(embed)
        response = webhook.execute()
        if response.status_code == 204:
            logging.info("Notification sent successfully.")
        else:
            logging.warning(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")


def run_detection():
    """
    Periodically fetch and filter tokens, sending notifications for matches.
    """
    logging.info("Starting detection process...")
    while True:
        tokens = fetch_tokens()
        filtered_tokens = filter_tokens(tokens)
        for token in filtered_tokens:
            send_discord_notification(token)
        time.sleep(POLL_INTERVAL)


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the bot is running.
    """
    return jsonify({"status": "healthy", "message": "Trading bot is operational."}), 200


if __name__ == "__main__":
    # Run the detection process in the background and Flask for health checks
    from threading import Thread
    detection_thread = Thread(target=run_detection)
    detection_thread.daemon = True
    detection_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
