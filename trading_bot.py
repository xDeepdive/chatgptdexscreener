from flask import Flask, request, jsonify
import logging

# Initialize Flask App
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.route("/trade", methods=["POST"])
def trade_handler():
    """
    Handle trading bot data sent from the detection bot.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        contract_address = data.get("contract_address")
        symbol = data.get("symbol")

        if not contract_address or not symbol:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: 'contract_address' and 'symbol'"
            }), 400

        # Log the received trade data
        logging.info(f"Received trade data: {symbol} ({contract_address})")

        # Simulate processing the trade data (e.g., saving it or further processing)
        return jsonify({"status": "success", "message": "Trade data received."}), 200
    except Exception as e:
        logging.error(f"Error processing trade data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=10000)
