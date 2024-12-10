from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/trade", methods=["POST"])
def trade():
    """
    Receive trade requests from the detection bot and simulate trading actions.
    """
    try:
        data = request.json
        print(f"Received payload: {data}")
        contract_address = data.get("contract_address")
        token_symbol = data.get("symbol")

        if not contract_address or not token_symbol:
            return jsonify({"error": "Invalid payload"}), 400

        print(f"Processing trade for {token_symbol} at address {contract_address}")
        # Simulated trading logic can go here
        return jsonify({"status": "success", "message": f"Trade initiated for {token_symbol}"}), 200
    except Exception as e:
        print(f"Error in /trade endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(port=5000)
