import os
import pandas as pd
from fyers_apiv3.fyersModel import FyersModel
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")

# === Initialize Fyers client ===
fyers = FyersModel(client_id=FYERS_CLIENT_ID, token=FYERS_ACCESS_TOKEN, log_path="")

# === Generate Option Symbols ===
def generate_symbols(expiry="24J18", strikes=range(17800, 18201, 100), base="NSE:NIFTY"):
    ce = [f"{base}{expiry}{strike}CE" for strike in strikes]
    pe = [f"{base}{expiry}{strike}PE" for strike in strikes]
    return ce + pe

# === Batch API Fetch ===
def fetch_quotes(symbols):
    all_data = []
    for i in range(0, len(symbols), 10):  # Fyers limit is 10 per request
        batch = symbols[i:i + 10]
        try:
            res = fyers.quotes({"symbols": ",".join(batch)})
            if res.get("s") == "ok":
                all_data.extend(res["d"])
            else:
                print("⚠️ API error:", res)
        except Exception as e:
            print(f"❌ Exception on batch: {e}")
    return all_data

# === Build Data Table ===
def build_table(data):
    rows = []
    for item in data:
        try:
            v = item["v"]
            name = item["n"]
            strike = int(v.get("strikePrice", 0))
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
        except Exception as e:
            print(f"⚠️ Error parsing item: {item} → {e}")
    return rows

# === Main Execution ===
def main():
    expiry = "24J18"  # Change this to the desired expiry
    strikes = range(17800, 18201, 100)
    symbols = generate_symbols(expiry, strikes)

    print("🔄 Fetching option chain for:", expiry)
    data = fetch_quotes(symbols)
    table = build_table(data)
    df = pd.DataFrame(table)

    if df.empty:
        print("⚠️ No valid data retrieved. Nothing saved.")
        return

    print("✅ Columns:", df.columns.tolist())
    print("📊 Rows fetched:", len(df))

    # Pivot format
    df_pivot = pd.pivot_table(
        df,
        index="Strike",
        columns="Type",
        values=[
            "Symbol", "LTP", "Qty", "Chg", "%Chg", "Volume", "OI",
            "Contracts", "OI Chg", "%OI Chg", "IV", "Prev OI"
        ],
        aggfunc="first"
    )

    df_pivot.columns = [f"{col[1]}_{col[0]}" for col in df_pivot.columns]
    df_pivot.reset_index(inplace=True)

    file_name = f"NIFTY_Option_Chain_{expiry}.xlsx"
    df_pivot.to_excel(file_name, index=False)
    print(f"✅ Saved to: {file_name}")

if __name__ == "__main__":
    main()
