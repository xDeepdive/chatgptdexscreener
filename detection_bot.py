import requests

# Trading bot webhook URL
TRADING_BOT_WEBHOOK = "https://trading-bot-v0nx.onrender.com/trade"

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
            return response.json()  # Assuming it's a list
        else:
            print(f"Error fetching tokens: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error during fetch: {e}")
        return []

def filter_tokens(tokens):
    """
    Filter tokens based on available fields in the API response.
    """
    qualified_tokens = []
    for token in tokens:
        try:
            # Example filters:
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
            print(f"Successfully sent {token_symbol} to trading bot!")
        else:
            print(f"Failed to send {token_symbol}. Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending to trading bot: {e}")

def main():
    """
    Main function to fetch, filter, and send tokens to the trading bot.
    """
    tokens = fetch_tokens()
    if not tokens:
        print("No tokens fetched. Exiting...")
        return

    qualified_tokens = filter_tokens(tokens)
    for token in qualified_tokens:
        send_to_trading_bot(token["contract_address"], token["symbol"])

if __name__ == "__main__":
    main()
