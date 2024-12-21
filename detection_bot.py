import requests
import time
import logging
from discord_webhook import DiscordWebhook, DiscordEmbed

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/search?q=solana"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"
POLL_INTERVAL = 30  # Polling interval in seconds
NOTIFICATION_BATCH_SIZE = 5  # Number of tokens per batch
BATCH_DELAY = 2  # Delay between batches in seconds

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_tokens():
    """
    Fetch the latest token data from DexScreener using the /search endpoint for Solana.
    """
    try:
        logging.info("Fetching tokens from DexScreener...")
        response = requests.get(DEXSCREENER_API_URL)
        response.raise_for_status()
        tokens = response.json().get("pairs", [])
        logging.info(f"Fetched {len(tokens)} tokens.")
        return tokens
    except Exception as e:
        logging.error(f"Error fetching tokens: {e}")
        return []


def send_discord_notifications(tokens):
    """
    Send Discord notifications for a batch of tokens.
    """
    try:
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        for token in tokens:
            base_token = token.get("baseToken", {})
            volume_24h_usd = token.get("volume", {}).get("usd", "N/A")
            url = token.get("url", "https://dexscreener.com")
            contract_address = base_token.get("address", "N/A")
            token_name = base_token.get("name", "Unknown")
            token_symbol = base_token.get("symbol", "N/A")

            embed = DiscordEmbed(
                title=f"🚀 New Token Alert: {token_name} ({token_symbol})",
                description=(
                    f"**24h Volume (USD)**: ${volume_24h_usd}\n"
                    f"**Chain**: {token.get('chainId', 'N/A')}\n"
                    f"**Contract Address**: `{contract_address}`\n"
                    f"[🔗 View on DexScreener]({url})"
                ),
                color=0x00ff00,
            )
            webhook.add_embed(embed)

        response = webhook.execute()
        if response.status_code == 200:
            logging.info("Batch notification sent successfully.")
        elif response.status_code == 429:
            retry_after = response.json().get("retry_after", 1)
            logging.warning(f"Rate limit hit. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return send_discord_notifications(tokens)
        else:
            logging.warning(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending Discord notifications: {e}")


def run_detection():
    """
    Periodically fetch tokens and send notifications in batches.
    """
    logging.info("Starting detection process...")
    while True:
        tokens = fetch_tokens()
        if not tokens:
            logging.error("No tokens fetched. Skipping this cycle.")
            time.sleep(POLL_INTERVAL)
            continue

        # Send notifications in batches
        for i in range(0, len(tokens), NOTIFICATION_BATCH_SIZE):
            batch = tokens[i:i + NOTIFICATION_BATCH_SIZE]
            send_discord_notifications(batch)
            time.sleep(BATCH_DELAY)  # Delay between batches to avoid rate limits

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    # Start the detection process
    run_detection()
