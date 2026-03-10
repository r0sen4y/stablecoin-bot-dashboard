import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time

# -------------------
# App Settings
# -------------------
st.set_page_config(layout="wide")
st.title("Live Stablecoin Simulation Dashboard")
st.markdown("""
Simulates a virtual portfolio of stablecoins (USDT, USDC, DAI)  
with minor low-risk trades and live real-market prices from CoinGecko.
""")

# -------------------
# Simulation Parameters
# -------------------
interval_minutes = 5
drift_threshold = 0.02  # 2% drift triggers alert

# -------------------
# Helper Functions
# -------------------
def get_stablecoin_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "tether,usd-coin,dai",
        "vs_currencies": "eur"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return {
            "USDT": data["tether"]["eur"],
            "USDC": data["usd-coin"]["eur"],
            "DAI": data["dai"]["eur"]
        }
    except Exception:
        return {"USDT":1.0,"USDC":1.0,"DAI":1.0}

# -------------------
# Initialize Data Storage
# -------------------
if 'price_df' not in st.session_state:
    st.session_state.price_df = pd.DataFrame(columns=['time','USDT','USDC','DAI'])
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'USDT':500, 'USDC':0, 'DAI':0, 'value_history':[]}
if 'log' not in st.session_state:
    st.session_state.log = []

placeholder_chart = st.empty()
alert_box = st.empty()
log_box = st.empty()

# -------------------
# Main Live Loop
# -------------------
while True:
    now = datetime.now()
    prices = get_stablecoin_prices()
    USDT, USDC, DAI = prices['USDT'], prices['USDC'], prices['DAI']

    # Add new row to the price dataframe
    new_row = pd.DataFrame([{
        'time': now,
        'USDT': USDT,
        'USDC': USDC,
        'DAI': DAI
    }])
    st.session_state.price_df = pd.concat([st.session_state.price_df, new_row], ignore_index=True)

    # -------------------
    # Drift alerts
    # -------------------
    alerts = []
    for coin, price in prices.items():
        if abs(price - 1) > drift_threshold:
            alerts.append(f"{coin} drift {price:.3f}")
            st.session_state.log.append(f"{now} ALERT: {coin} drift {price:.3f}")
    if alerts:
        alert_box.warning("\n".join(alerts))
    else:
        alert_box.success("No significant drift detected.")

    # -------------------
    # Minor simulated trades
    # -------------------
    total_value = (
        st.session_state.portfolio['USDT']*USDT +
        st.session_state.portfolio['USDC']*USDC +
        st.session_state.portfolio['DAI']*DAI
    )
    move = 0.01*total_value
    # simple rotation USDT → USDC → DAI
    if st.session_state.portfolio['USDT']*USDT > 0:
        sell = min(st.session_state.portfolio['USDT'], move/USDT)
        st.session_state.portfolio['USDT'] -= sell
        st.session_state.portfolio['USDC'] += sell
        st.session_state.log.append(f"{now} TRADE: {sell:.2f} USDT → USDC")

    # record portfolio total
    total_value = (
        st.session_state.portfolio['USDT']*USDT +
        st.session_state.portfolio['USDC']*USDC +
        st.session_state.portfolio['DAI']*DAI
    )
    st.session_state.portfolio['value_history'].append(total_value)

    # -------------------
    # Plotting with Streamlit
    # -------------------
    df = st.session_state.price_df.set_index('time')
    st.subheader("Stablecoin Prices (EUR)")
    st.line_chart(df)

    st.subheader("Portfolio Value (€)")
    st.line_chart(pd.DataFrame({'Portfolio': st.session_state.portfolio['value_history']}))

    # show last 10 log entries
    log_box.text("\n".join(st.session_state.log[-10:]))

    time.sleep(interval_minutes*60)
