import requests
import time
import logging
from discord_webhook import DiscordWebhook, DiscordEmbed

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/search?q=solana"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd"  # Predefined webhook URL
POLL_INTERVAL = 60  # Polling interval in seconds

# Criteria for filtering tokens
TOKEN_CRITERIA = {
    "min_liquidity_sol": 500,  # Minimum liquidity in SOL
    "chain": "solana",         # Target blockchain
}

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_tokens():
    """
    Fetch the latest token data from DexScreener using the /search endpoint.
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


def filter_tokens(tokens):
    """
    Filter tokens based on liquidity in SOL and chain criteria.
    """
    filtered_tokens = []
    for token in tokens:
        try:
            chain = token.get("chainId", "").lower()
            base_amount = token.get("liquidity", {}).get("base", 0)  # Amount of Solana in the pool

            logging.info(
                f"Token: {token.get('baseToken', {}).get('symbol', 'N/A')}, "
                f"Liquidity (SOL): {base_amount}, Chain: {chain}"
            )

            # Filter by chain and liquidity criteria
            if chain == TOKEN_CRITERIA["chain"] and base_amount >= TOKEN_CRITERIA["min_liquidity_sol"]:
                filtered_tokens.append(token)
            else:
                logging.debug(
                    f"Rejected Token: {token.get('baseToken', {}).get('symbol', 'N/A')} - "
                    f"Liquidity (SOL): {base_amount}, Chain: {chain}"
                )
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
        base_token = token.get("baseToken", {})
        liquidity_sol = token.get("liquidity", {}).get("base", 0)
        url = token.get("url", "https://dexscreener.com")

        logging.info(f"Sending Discord notification for token: {base_token.get('symbol', 'N/A')}")
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(
            title=f"🚀 New Token Alert: {base_token.get('name', 'N/A')} ({base_token.get('symbol', 'N/A')})",
            description=(
                f"**Liquidity (SOL)**: {liquidity_sol:,.2f}\n"
                f"**Chain**: {token.get('chainId', 'N/A')}\n"
                f"[🔗 View on DexScreener]({url})"
            ),
            color=0x00ff00,
        )
        webhook.add_embed(embed)
        response = webhook.execute()

        if response.status_code == 200:
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
        if not tokens:
            logging.error("No tokens fetched. Skipping this cycle.")
            time.sleep(POLL_INTERVAL)
            continue

        filtered_tokens = filter_tokens(tokens)
        for token in filtered_tokens:
            send_discord_notification(token)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    # Start the detection process
    run_detection()
