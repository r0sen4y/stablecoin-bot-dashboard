import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

# -------------------
# App Settings
# -------------------
st.set_page_config(layout="wide")
st.title("Live Stablecoin Simulation Dashboard")
st.markdown("""
Simulates low‑risk stablecoin portfolio (USDT, USDC, DAI)  
with minor automated trades and drift alerts.
""")

# -------------------
# Simulation Parameters
# -------------------
interval_minutes = 5
drift_threshold = 0.02  # 2%

# -------------------
# Initialize Exchange
# -------------------
exchange = ccxt.kraken()

# -------------------
# Helper Functions
# -------------------
def fetch_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception:
        return None

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
# Main Live Loop (runs every 5 minutes)
# -------------------
while True:
    now = datetime.now()
    usdt = fetch_price('USDT/EUR')
    usdc = fetch_price('USDC/EUR')
    dai  = fetch_price('DAI/EUR')
    
    st.session_state.price_df = st.session_state.price_df.append({
        'time': now,
        'usdt': usdt or 1.0,
        'usdc': usdc or 1.0,
        'dai': dai or 1.0
    }, ignore_index=True)

    # -------------------
    # Drift alerts
    # -------------------
    alerts = []
    for coin, price in [('USDT',usdt), ('USDC',usdc), ('DAI',dai)]:
        if price and abs(price - 1) > drift_threshold:
            alerts.append(f"{coin} drift {price:.3f}")
            st.session_state.log.append(f"{now} ALERT: {coin} drift {price:.3f}")

    if alerts:
        alert_box.warning("\n".join(alerts))
    else:
        alert_box.success("No significant drift detected.")

    # -------------------
    # Minor simulated trades (between coins)
    # -------------------
    # Random tiny moves: 1‑2% between assets
    total_value = (
        st.session_state.portfolio['usdt'] * (usdt or 1.0) +
        st.session_state.portfolio['usdc'] * (usdc or 1.0) +
        st.session_state.portfolio['dai']  * (dai  or 1.0)
    )
    # Simple rotation logic
    if usdt and usdc and dai:
        # rotate 1% between coins
        move = 0.01 * total_value
        # example cycle: USDT → USDC → DAI
        if st.session_state.portfolio['usdt']*usdt > 0:
            sell = min(st.session_state.portfolio['usdt'], move/usdt)
            st.session_state.portfolio['usdt'] -= sell
            st.session_state.portfolio['usdc'] += sell
            st.session_state.log.append(f"{now} TRADE: {sell:.2f} USDT → USDC")

    # record portfolio total
    total_value = (
        st.session_state.portfolio['usdt'] * (usdt or 1.0) +
        st.session_state.portfolio['usdc'] * (usdc or 1.0) +
        st.session_state.portfolio['dai']  * (dai  or 1.0)
    )
    st.session_state.portfolio['value_history'].append(total_value)

    # -------------------
    # Plotting
    # -------------------
    df = st.session_state.price_df.copy()
    fig, ax1 = plt.subplots()
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
