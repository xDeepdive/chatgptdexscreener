import requests
from datetime import datetime

try:
    import telegram
except ModuleNotFoundError:
    raise ImportError("The 'telegram' module is not installed. Install it using 'pip install python-telegram-bot'.")

# Telegram Bot Token and Chat ID
TELEGRAM_BOT_TOKEN = "8116367888:AAEd5fYDGqrI-QjvOfw95tc_N9IJjnoo89o"
TELEGRAM_CHAT_ID = "5067817541"  # Replace with your chat ID

TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"


def send_telegram_notification(message):
    """
    Send a message to the configured Telegram chat.
    """
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Telegram notification sent: {message}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")


def fetch_tokens():
    """
    Fetch token profiles from the updated Dexscreener API endpoint.
    """
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        print(f"Fetching tokens from {url}...")
        if response.status_code == 200:
            print("Tokens fetched successfully!")
            send_telegram_notification("✅ Tokens fetched successfully from Dexscreener!")
            return response.json()  # Assuming it's a list
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
    Filter tokens based on available fields in the API response.
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
    Send the qualified token data to the trading bot.
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


def main():
    """
    Main function to fetch, filter, and send tokens to the trading bot.
    """
    send_telegram_notification("🚀 Detection bot is now live and monitoring tokens!")
    tokens = fetch_tokens()
    if not tokens:
        print("No tokens fetched. Exiting...")
        return

    qualified_tokens = filter_tokens(tokens)
    for token in qualified_tokens:
        send_to_trading_bot(token["contract_address"], token["symbol"])


if __name__ == "__main__":
    main()
