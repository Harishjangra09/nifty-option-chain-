from flask import Flask, jsonify
import os
import pandas as pd
import requests
from dotenv import load_dotenv
from fyers_apiv3.fyersModel import FyersModel

load_dotenv()

FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")
fyers = FyersModel(client_id=FYERS_CLIENT_ID, token=FYERS_ACCESS_TOKEN, log_path="")

app = Flask(__name__)

# === Generate Option Symbols ===
def generate_symbols(expiry="24J18", strikes=range(17800, 18201, 100), base="NSE:NIFTY"):
    ce = [f"{base}{expiry}{strike}CE" for strike in strikes]
    pe = [f"{base}{expiry}{strike}PE" for strike in strikes]
    return ce + pe

# === Fetch Quotes ===
def fetch_quotes(symbols):
    all_data = []
    for i in range(0, len(symbols), 10):
        batch = symbols[i:i+10]
        res = fyers.quotes({"symbols": ",".join(batch)})
        if res.get("s") == "ok":
            all_data.extend(res["d"])
    return all_data

# === Format Option Chain Table ===
def build_table(data):
    rows = []
    for item in data:
        v = item["v"]
        name = item["n"]
        strike = v.get("strikePrice")
        option_type = "CE" if "CE" in name else "PE"
        row = {
            "Strike": strike,
            "Symbol": name,
            "Type": option_type,
            "LTP": v.get("lp", ""),
            "Qty": v.get("qty", ""),
            "Chg": v.get("ch", ""),
            "%Chg": v.get("chp", ""),
            "Volume": v.get("volume", ""),
            "OI": v.get("oi", ""),
            "Contracts": v.get("contracts", ""),
            "OI Chg": v.get("oi_day_change", ""),
            "%OI Chg": v.get("oi_day_perc_change", ""),
            "IV": v.get("iv", ""),
            "Prev OI": v.get("prev_oi", "")
        }
        rows.append(row)
    return rows

# === Expose as API ===
@app.route("/")
def home():
    return "🟢 NIFTY Option Chain API is live!"

@app.route("/optionchain")
def option_chain():
    expiry = "24J18"
    strikes = range(17800, 18201, 100)
    symbols = generate_symbols(expiry, strikes)
    data = fetch_quotes(symbols)
    table = build_table(data)
    return jsonify(table)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
