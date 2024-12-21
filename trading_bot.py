import requests
from flask import Flask, request
import os
import threading
import time

# Environment Variables
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1319642099137773619/XWWaswRKfriT6YaYT4SxYeIxBvhDVZAN0o22LVc8gifq5Y4RPK7q70_lUDflqEz3REKd")
TRADING_BOT_WEBHOOK = os.getenv("TRADING_BOT_WEBHOOK", "https://trading-bot-v0nx.onrender.com/trade")

# Initialize Flask App
app = Flask(__name__)

@app.route("/", methods=["POST", "HEAD"])
def webhook():
    """
    Handle incoming webhook messages (if needed for future extensions).
    """
    return "Webhook endpoint is live.", 200


def send_discord_notification(message):
    """
    Send a message to the configured Discord webhook.
    """
    try:
        payload = {"content": message}
        headers = {"Content-Type": "application/json"}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code == 204:
            print(f"Discord notification sent: {message}")
        else:
            print(f"Error sending Discord notification: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")


def fetch_tokens():
    """
    Fetch token profiles from the Dexscreener API endpoint.
    """
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        print(f"Fetching tokens from {url}...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Tokens fetched successfully!")
            send_discord_notification("✅ Tokens fetched successfully from Dexscreener!")
            return response.json()
        else:
            error_message = f"Error fetching tokens: {response.status_code} - {response.text}"
            print(error_message)
            send_discord_notification(f"❌ {error_message}")
            return []
    except Exception as e:
        error_message = f"Error during fetch: {e}"
        print(error_message)
        send_discord_notification(f"❌ {error_message}")
        return []


def filter_tokens(tokens):
    """
    Filter tokens based on specific criteria.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            # Extract relevant fields
            chain_id = token.get("chainId", "")
            token_address = token.get("tokenAddress", "")
            description = token.get("description", "Unknown")
            market_cap = token.get("marketCapUSD", 0)
            liquidity = token.get("liquidityUSD", 0)
            socials = token.get("links", [])

            # Check if token has required social links
            has_socials = any(link.get("type", "").lower() in ["telegram", "twitter"] for link in socials)

            # Apply criteria
            if (
                chain_id == "solana" and
                market_cap >= 2_000_000 and
                liquidity >= 600_000 and
                has_socials
            ):
                print(f"Token qualified: {description} (Address: {token_address})")
                qualified_tokens.append({
                    "contract_address": token_address,
                    "symbol": description,
                    "market_cap": market_cap,
                    "liquidity": liquidity
                })
            else:
                print(f"Token did not meet criteria: {description} (Address: {token_address})")
        except Exception as e:
            print(f"Error processing token: {e}")

    if not qualified_tokens:
        print("No tokens qualified based on the criteria.")
        send_discord_notification("⚠️ No tokens qualified based on the criteria.")
    return qualified_tokens


def send_to_trading_bot(contract_address, token_symbol):
    """
    Send qualified tokens to the trading bot.
    """
    payload = {"contract_address": contract_address, "symbol": token_symbol}
    try:
        print(f"Attempting to send to trading bot: {payload}")
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 200:
            success_message = f"✅ Successfully sent {token_symbol} ({contract_address}) to trading bot!"
            print(success_message)
            send_discord_notification(success_message)
        else:
            error_message = f"❌ Failed to send {token_symbol}. Response: {response.status_code} - {response.text}"
            print(error_message)
            send_discord_notification(error_message)
    except Exception as e:
        error_message = f"❌ Error sending {token_symbol} to trading bot: {e}"
        print(error_message)
        send_discord_notification(error_message)


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
                    send_to_trading_bot(token["contract_address"], token["symbol"])
        except Exception as e:
            print(f"Error in token fetching loop: {e}")
        finally:
            time.sleep(300)  # Fetch every 5 minutes


if __name__ == "__main__":
    # Run Flask app and token fetching in separate threads
    threading.Thread(target=start_fetching_tokens).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
