def filter_tokens(tokens):
    """
    Filter tokens based on 24-hour trading volume and ensure they are on the Solana chain.
    """
    filtered_tokens = []
    for token in tokens:
        try:
            chain = token.get("chainId", "").lower()
            volume_24h_usd = token.get("volume", {}).get("usd", 0)  # 24-hour trading volume in USD
            base_token = token.get("baseToken", {})
            contract_address = base_token.get("address", "N/A")
            token_name = base_token.get("name", "Unknown")
            token_symbol = base_token.get("symbol", "N/A")

            # Log all token data for debugging
            logging.info(f"Token: {token_name} ({token_symbol}), 24h Volume (USD): ${volume_24h_usd}, Chain: {chain}")

            # Check for chain mismatch
            if chain != TOKEN_CRITERIA["chain"]:
                logging.debug(
                    f"Rejected Token: {token_name} ({token_symbol}) - Chain mismatch: {chain} - Contract: {contract_address}"
                )
                continue

            # Check for volume criteria
            if volume_24h_usd < TOKEN_CRITERIA["min_volume_usd_24h"]:
                logging.debug(
                    f"Rejected Token: {token_name} ({token_symbol}) - Low 24h Volume: ${volume_24h_usd:,.2f} - Contract: {contract_address}"
                )
                continue

            filtered_tokens.append(token)
        except KeyError as e:
            logging.error(f"Key error during token filtering: {e}")
            continue
    logging.info(f"{len(filtered_tokens)} tokens match the criteria.")
    return filtered_tokens
