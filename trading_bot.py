from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    """
    Health check endpoint to verify the trading bot service is running.
    """
    return jsonify({"status": "success", "message": "Trading bot is live!"}), 200

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
        print(f"Received trade data: {symbol} ({contract_address})")

        # Simulate processing the trade data (Add your logic here if necessary)
        # Example: Forwarding data to another service or saving in a database

        return jsonify({"status": "success", "message": "Trade data received."}), 200
    except Exception as e:
        print(f"Error processing trade data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
