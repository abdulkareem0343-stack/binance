import pandas as pd
import ta
import ccxt
import streamlit as st

st.set_page_config(page_title="Binance 15m RSI Scanner", layout="wide")
st.title("🔥 Binance Top Gainers + RSI (30 - 50) Filter")
st.write("15-Minute Timeframe par Scanner Live")

# Binance Futures Public API (Bypasses Regional Restrictions on Streamlit Cloud)
exchange = ccxt.binanceusdm({
    'enableRateLimit': True,
    'timeout': 30000,
})

def fetch_filtered_coins():
    try:
        tickers = exchange.fetch_tickers()
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return pd.DataFrame()

    gainers = []
    for symbol, ticker in tickers.items():
        # Filtering USDT pairs and 24h gainers (>0%)
        if symbol.endswith('/USDT:USDT') or symbol.endswith('/USDT'):
            if ticker.get('percentage') is not None and ticker['percentage'] > 0:
                clean_symbol = symbol.split(':')[0]
                gainers.append({
                    'raw_symbol': symbol,
                    'symbol': clean_symbol,
                    'change_24h': round(ticker['percentage'], 2),
                    'price': ticker['last']
                })
    
    gainers = sorted(gainers, key=lambda x: x['change_24h'], reverse=True)
    matching_coins = []

    status_text = st.empty()
    progress_bar = st.progress(0)
    
    total = len(gainers)
    for i, item in enumerate(gainers):
        status_text.text(f"Scanning {item['symbol']} ({i+1}/{total})...")
        progress_bar.progress((i + 1) / total)
        
        try:
            ohlcv = exchange.fetch_ohlcv(item['raw_symbol'], timeframe='15m', limit=50)
            if not ohlcv or len(ohlcv) < 15:
                continue
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            latest_rsi = round(df['rsi'].iloc[-1], 2)
            
            # Condition: RSI between 30 and 50
            if 30 <= latest_rsi <= 50:
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

if st.button("🚀 Start Scan / Refresh"):
    with st.spinner("Scanning Binance Market..."):
        df_result = fetch_filtered_coins()
        
        if not df_result.empty:
            st.success(f"Found {len(df_result)} Token(s) Matching Criteria!")
            st.dataframe(df_result, use_container_width=True)
        else:
            st.warning("Abhi koi aisa Gainer coin nahi mila jiska 15m RSI 30-50 ke beech ho.")
