import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit as st
import time

st.set_page_config(page_title="Binance 15m RSI Scanner", layout="wide")
st.title("🔥 Binance Top Gainers + RSI (30 - 40) Filter")
st.write("15-Minute Timeframe par Scanner Live")

# Binance Exchange Initialize
exchange = ccxt.binance({'enableRateLimit': True})

def fetch_filtered_coins():
    # 1. Fetch 24h tickers
    tickers = exchange.fetch_tickers()
    
    # 2. Filter USDT Pairs & 24h Gainers (> 0% Change)
    gainers = []
    for symbol, ticker in tickers.items():
        if symbol.endswith('/USDT') and ticker.get('percentage') is not None:
            if ticker['percentage'] > 0:  # Gainer condition
                gainers.append({
                    'symbol': symbol,
                    'change_24h': round(ticker['percentage'], 2),
                    'price': ticker['last']
                })
    
    # Sort gainers by highest percentage
    gainers = sorted(gainers, key=lambda x: x['change_24h'], reverse=True)
    
    matching_coins = []

    # 3. Fetch 15m OHLCV and Calculate RSI (14)
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    total = len(gainers)
    for i, item in enumerate(gainers):
        status_text.text(f"Scanning {item['symbol']} ({i+1}/{total})...")
        progress_bar.progress((i + 1) / total)
        
        try:
            # Fetch last 50 candles of 15m timeframe
            ohlcv = exchange.fetch_ohlcv(item['symbol'], timeframe='15m', limit=50)
            if not ohlcv or len(ohlcv) < 15:
                continue
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate RSI (14)
            df['rsi'] = ta.rsi(df['close'], length=14)
            latest_rsi = round(df['rsi'].iloc[-1], 2)
            
            # 4. Condition: RSI between 30 and 40
            if 30 <= latest_rsi <= 40:
                matching_coins.append({
                    'Symbol': item['symbol'],
                    '24h Change (%)': f"+{item['change_24h']}%",
                    'Current Price': item['price'],
                    'RSI (15m)': latest_rsi
                })
        except Exception:
            continue
            
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(matching_coins)

# UI Refresh Button
if st.button("🚀 Start Scan / Refresh"):
    with st.spinner("Scanning Binance Market..."):
        df_result = fetch_filtered_coins()
        
        if not df_result.empty:
            st.success(f"Found {len(df_result)} Token(s) Matching Criteria!")
            st.dataframe(df_result, use_container_width=True)
        else:
            st.warning("Abhi koi aisa Gainer coin nahi mila jiska 15m RSI 30-40 ke beech ho.")
