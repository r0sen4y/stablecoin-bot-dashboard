import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
with minor low-risk trades and live real-market prices.
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
            "usdt": data["tether"]["eur"],
            "usdc": data["usd-coin"]["eur"],
            "dai": data["dai"]["eur"]
        }
    except Exception:
        # fallback to 1.0 if API fails
        return {"usdt": 1.0, "usdc": 1.0, "dai": 1.0}

# -------------------
# Data Storage
# -------------------
if 'price_df' not in st.session_state:
    st.session_state.price_df = pd.DataFrame(columns=['time','usdt','usdc','dai'])
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'usdt': 500, 'usdc': 0, 'dai': 0, 'value_history': []}
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
    usdt, usdc, dai = prices['usdt'], prices['usdc'], prices['dai']

    # record prices
    st.session_state.price_df = st.session_state.price_df.append({
        'time': now,
        'usdt': usdt,
        'usdc': usdc,
        'dai': dai
    }, ignore_index=True)

    # -------------------
    # Drift alerts
    # -------------------
    alerts = []
    for coin, price in [('USDT',usdt), ('USDC',usdc), ('DAI',dai)]:
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
        st.session_state.portfolio['usdt'] * usdt +
        st.session_state.portfolio['usdc'] * usdc +
        st.session_state.portfolio['dai']  * dai
    )

    # Simple rotation logic: move 1% of total portfolio between coins
    move = 0.01 * total_value
    if st.session_state.portfolio['usdt']*usdt > 0:
        sell = min(st.session_state.portfolio['usdt'], move/usdt)
        st.session_state.portfolio['usdt'] -= sell
        st.session_state.portfolio['usdc'] += sell
        st.session_state.log.append(f"{now} TRADE: {sell:.2f} USDT → USDC")

    # record portfolio total
    total_value = (
        st.session_state.portfolio['usdt'] * usdt +
        st.session_state.portfolio['usdc'] * usdc +
        st.session_state.portfolio['dai']  * dai
    )
    st.session_state.portfolio['value_history'].append(total_value)

    # -------------------
    # Plotting
    # -------------------
    df = st.session_state.price_df.copy()
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(df['time'], df['usdt'], label="USDT Price")
    ax1.plot(df['time'], df['usdc'], label="USDC Price")
    ax1.plot(df['time'], df['dai'],  label="DAI Price")
    ax1.set_ylabel("Price (€)")
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(df['time'], st.session_state.portfolio['value_history'], color='green', label="Portfolio Value")
    ax2.set_ylabel("Portfolio Value (€)")
    ax2.legend(loc='upper right')

    placeholder_chart.pyplot(fig)
    log_box.text("\n".join(st.session_state.log[-10:]))

    time.sleep(interval_minutes * 60)
