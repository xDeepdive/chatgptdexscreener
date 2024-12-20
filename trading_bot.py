from flask import Flask, request, jsonify
import logging
from datetime import datetime

# Initialize Flask App
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log"),  # Log to file
        logging.StreamHandler()                 # Log to console
    ]
)

@app.route("/trade", methods=["POST"])
def trade_handler():
    """
    Handle trading bot data sent from the detection bot.
    """
    try:
        # Parse JSON payload
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        # Extract required fields
        contract_address = data.get("contract_address")
        symbol = data.get("symbol")
        additional_info = data.get("additional_info", "No additional information provided")

        # Validate fields
        if not contract_address or not symbol:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: 'contract_address' and 'symbol'"
            }), 400

        # Log the received trade data
        logging.info(f"Received trade data: {symbol} ({contract_address})")
        logging.info(f"Additional Info: {additional_info}")

        # Simulate processing the trade data
        # Add your processing logic here (e.g., saving to DB or forwarding)
        processing_result = process_trade_data(contract_address, symbol, additional_info)

        # Return success response
        return jsonify({"status": "success", "message": processing_result}), 200
    except Exception as e:
        logging.error(f"Error processing trade data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def process_trade_data(contract_address, symbol, additional_info):
    """
    Simulate processing the trade data.
    This can be expanded to include database integration or further processing.
    """
    # Placeholder logic for processing
    processing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Processing trade data for {symbol} ({contract_address}) at {processing_time}")
    return f"Trade data for {symbol} successfully processed at {processing_time}"


@app.route("/", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the trading bot service is running.
    """
    return jsonify({"status": "success", "message": "Trading bot is live!"}), 200


if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=10000)
