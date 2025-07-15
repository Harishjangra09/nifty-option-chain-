import os
import pandas as pd
from fyers_apiv3.fyersModel import FyersModel  # ✅ Correct import
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID")

# === Initialize Fyers client ===
fyers = FyersModel(client_id=FYERS_CLIENT_ID, token=FYERS_ACCESS_TOKEN, log_path="")

# === Generate NIFTY Option Symbols ===
def generate_symbols(expiry="24J18", strikes=range(17800, 18201, 100), base="NSE:NIFTY"):
    ce, pe = [], []
    for strike in strikes:
        ce.append(f"{base}{expiry}{strike}CE")
        pe.append(f"{base}{expiry}{strike}PE")
    return ce + pe

# === Fetch data in batches ===
def fetch_quotes(symbols):
    all_data = []
    for i in range(0, len(symbols), 10):
        batch = symbols[i:i + 10]
        try:
            res = fyers.quotes({"symbols": ",".join(batch)})  # ✅ Fixed syntax
            if res["s"] == "ok":
                all_data.extend(res["d"])
            else:
                print("⚠️ API error:", res)
        except Exception as e:
            print(f"❌ Error fetching batch: {e}")
    return all_data

# === Build option chain table ===
def build_table(data):
    rows = []
    for item in data:
        try:
            v = item["v"]
            name = item["n"]
            strike = int(v["strikePrice"])
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
                "Prev OI CE": v.get("prev_oi", "") if option_type == "CE" else "",
                "Prev OI PE": v.get("prev_oi", "") if option_type == "PE" else "",
            }
            rows.append(row)
        except Exception as e:
            print(f"⚠️ Error parsing item: {item}, error: {e}")
    return rows

# === Main Execution ===
def main():
    expiry = "24J18"  # Update this manually if needed
    strikes = range(17800, 18201, 100)

    symbols = generate_symbols(expiry, strikes)
    print("🔄 Fetching option chain for:", expiry)
    
    data = fetch_quotes(symbols)
    table = build_table(data)

    df = pd.DataFrame(table)

    # Debug info
    print("✅ Columns:", df.columns.tolist())
    print("📊 Total rows:", len(df))

    # Create pivot only if valid data exists
    if not df.empty and "Symbol" in df.columns:
        df_pivot = pd.pivot_table(
            df,
            index="Strike",
            columns="Type",
            values=[
                "Symbol", "LTP", "Qty", "Chg", "%Chg", "Volume", "OI",
                "Contracts", "OI Chg", "%OI Chg", "IV", "Prev OI CE", "Prev OI PE"
            ],
            aggfunc="first"
        )
        df_pivot.columns = [f"{col[1]}_{col[0]}" for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        file_name = "NIFTY_Option_Chain.xlsx"
        df_pivot.to_excel(file_name, index=False)
        print(f"✅ Saved to: {file_name}")
    else:
        print("⚠️ No valid option chain data retrieved. Nothing saved.")

if __name__ == "__main__":
    main()
