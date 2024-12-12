import requests
from flask import Flask, request
from datetime import datetime
import os
import time  # For time.sleep functionality
from threading import Thread

try:
    import telegram
except ModuleNotFoundError:
    raise ImportError("The 'telegram' module is not installed. Install it using 'pip install python-telegram-bot'.")

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7617319742:AAHoKC5gxDKI5aOaEekS4bgiSfde4gKh0EI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5067817541")
TRADING_BOT_WEBHOOK = os.getenv("TRADING_BOT_WEBHOOK", "https://trading-bot-v0nx.onrender.com/trade")

# Initialize Flask App
app = Flask(__name__)

@app.route("/", methods=["POST", "HEAD", "GET"])
def webhook():
    """
    Handle incoming webhook messages from Telegram or other requests.
    """
    if request.method == "HEAD":
        return "", 200

    if request.method == "GET":
        return "Service is live!", 200

    try:
        update = telegram.Update.de_json(request.get_json(force=True), telegram.Bot(token=TELEGRAM_BOT_TOKEN))
        chat_id = update.message.chat.id
        message_text = update.message.text

        if message_text == "/start":
            send_telegram_notification("Hello! Detection bot is up and running.", chat_id)
        else:
            send_telegram_notification(f"You said: {message_text}", chat_id)

        return "OK"
    except Exception as e:
        print(f"Error handling webhook: {e}")
        return "Error", 500

def send_telegram_notification(message, chat_id=TELEGRAM_CHAT_ID):
    """
    Send a message to the configured Telegram chat.
    """
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=chat_id, text=message)
        print(f"Telegram notification sent: {message}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

def fetch_tokens():
    """
    Fetch token profiles from the Dexscreener API endpoint.
    """
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        print(f"Fetching tokens from {url}...")
        if response.status_code == 200:
            print("Tokens fetched successfully!")
            send_telegram_notification("✅ Tokens fetched successfully from Dexscreener!")
            return response.json()
        else:
            error_message = f"Error fetching tokens: {response.status_code} - {response.text}"
            print(error_message)
            send_telegram_notification(f"❌ {error_message}")
            return []
    except Exception as e:
        error_message = f"Error during fetch: {e}"
        print(error_message)
        send_telegram_notification(f"❌ {error_message}")
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
            has_twitter = any(link.get("type") == "twitter" for link in token.get("links", []))

            if chain_id == "solana" and description and has_twitter:
                print(f"Token qualified: {description} (Address: {token_address})")
                qualified_tokens.append({
                    "contract_address": token_address,
                    "symbol": description
                })
        except KeyError as e:
            print(f"Missing key in token data: {e}")

    if not qualified_tokens:
        print("No tokens qualified based on the criteria.")
        send_telegram_notification("⚠️ No tokens qualified based on the criteria.")
    return qualified_tokens

def send_to_trading_bot(contract_address, token_symbol):
    """
    Send qualified tokens to the trading bot.
    """
    payload = {"contract_address": contract_address, "symbol": token_symbol}
    try:
        print(f"Attempting to send to trading bot: {payload}")
        response = requests.post(TRADING_BOT_WEBHOOK, json=payload)
        if response.status_code == 200:
            success_message = f"✅ Successfully sent {token_symbol} ({contract_address}) to trading bot!"
            print(success_message)
            send_telegram_notification(success_message)
        else:
            error_message = f"❌ Failed to send {token_symbol}. Response: {response.status_code} - {response.text}"
            print(error_message)
            send_telegram_notification(error_message)
    except Exception as e:
        error_message = f"❌ Error sending {token_symbol} to trading bot: {e}"
        print(error_message)
        send_telegram_notification(error_message)

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
        time.sleep(300)  # Wait for 5 minutes before fetching tokens again

if __name__ == "__main__":
    # Start token fetching in a separate thread
    Thread(target=start_fetching_tokens).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
