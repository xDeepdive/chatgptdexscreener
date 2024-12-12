from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/trade', methods=['POST'])
def trade_handler():
    """
    Handle trading bot data sent from the detection bot.
    """
    try:
        data = request.json
        contract_address = data.get("contract_address")
        symbol = data.get("symbol")
        print(f"Received trade data: {symbol} ({contract_address})")
        return jsonify({"status": "success", "message": "Trade data received."}), 200
    except Exception as e:
        print(f"Error processing trade data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
