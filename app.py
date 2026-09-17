import pandas as pd
import ta
import ccxt
import streamlit as st

# Page Configuration for Mobile App Look
st.set_page_config(
    page_title="Crypto Scanner App",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Native Android App Interface
st.markdown("""
<style>
    /* Hide Streamlit default UI elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 500px !important;
    }
    
    /* Main App Background */
    body {
        background-color: #121212;
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Mobile App Top Header Bar */
    .app-header {
        background: #1e1e1e;
        padding: 15px 20px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 20px;
        border: 1px solid #2c2c2c;
    }
    .app-header-title {
        font-size: 18px;
        font-weight: 700;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .dev-tag {
        font-size: 11px;
        color: #2962ff;
        background: rgba(41, 98, 255, 0.15);
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: 600;
    }

    /* Mobile Coin Card */
    .coin-card {
        background: #1e1e1e;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #2a2a2a;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .symbol-title {
        font-size: 16px;
        font-weight: bold;
        color: #ffffff;
    }
    .gainer-tag {
        background-color: rgba(0, 200, 83, 0.15);
        color: #00e676;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
    }
    .card-bottom {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .price-text {
        font-size: 15px;
        font-weight: 600;
        color: #b0bec5;
    }
    .rsi-badge {
        background: linear-gradient(135deg, #2962ff 0%, #00b0ff 100%);
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Native App Action Button */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2962ff 0%, #1565c0 100%);
        color: white;
        font-weight: bold;
        border-radius: 14px;
        height: 52px;
        border: none;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(41, 98, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Mobile Top Header
st.markdown("""
<div class="app-header">
    <div>
        <div class="app-header-title">⚡ Crypto Scanner Pro</div>
        <div class="dev-tag">By Abdul Kareem</div>
    </div>
    <div style="font-size: 20px;">📱</div>
</div>
""", unsafe_allow_html=True)

# Controls inside a mobile expansion card
with st.expander("⚙️ Filter Options (Timeframe & RSI Range)", expanded=False):
    timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "4h"], index=0)
    rsi_min, rsi_max = st.slider("RSI Range", 0, 100, (30, 50))
    # Limit increased up to 250 coins
    top_gainers_count = st.slider("Scan Gainers Count", 20, 250, 100, step=10)

# Exchange setup
exchange = ccxt.kucoin({'enableRateLimit': True, 'timeout': 30000})

def fetch_filtered_coins():
    try:
        tickers = exchange.fetch_tickers()
    except Exception as e:
        st.error(f"Error connecting: {e}")
        return []

    gainers = []
    for symbol, ticker in tickers.items():
        if symbol.endswith('/USDT') and ticker.get('percentage') is not None:
            if ticker['percentage'] > 0:
                gainers.append({
                    'symbol': symbol,
                    'clean_symbol': symbol.replace('/USDT', ''),
                    'change_24h': round(ticker['percentage'], 2),
                    'price': ticker['last']
                })
    
    gainers = sorted(gainers, key=lambda x: x['change_24h'], reverse=True)
    matching_coins = []

    status = st.empty()
    progress = st.progress(0)
    limit = min(len(gainers), top_gainers_count)

    for i, item in enumerate(gainers[:limit]):
        status.caption(f"Scanning {item['clean_symbol']} ({i+1}/{limit})...")
        progress.progress((i + 1) / limit)
        
        try:
            ohlcv = exchange.fetch_ohlcv(item['symbol'], timeframe=timeframe, limit=50)
            if not ohlcv or len(ohlcv) < 15:
                continue
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            latest_rsi = round(df['rsi'].iloc[-1], 2)
            
            if rsi_min <= latest_rsi <= rsi_max:
                tv_link = f"https://www.tradingview.com/chart/?symbol=KUCOIN:{item['clean_symbol']}USDT"
                matching_coins.append({
                    'symbol': item['clean_symbol'],
                    'change_24h': item['change_24h'],
                    'price': item['price'],
                    'rsi': latest_rsi,
                    'chart': tv_link
                })
        except Exception:
            continue
            
    status.empty()
    progress.empty()
    return matching_coins

# Main Mobile Scan Trigger Button
if st.button("🚀 Start App Scan"):
    with st.spinner("Scanning Market..."):
        results = fetch_filtered_coins()
        
        if results:
            st.caption(f"Found {len(results)} Token(s) | Timeframe: {timeframe}")
            
            # Render App Cards
            for coin in results:
                st.markdown(f"""
                <div class="coin-card">
                    <div class="card-top">
                        <span class="symbol-title">🪙 {coin['symbol']}/USDT</span>
                        <span class="gainer-tag">+{coin['change_24h']}%</span>
                    </div>
                    <div class="card-bottom">
                        <span class="price-text">${coin['price']}</span>
                        <span class="rsi-badge">RSI: {coin['rsi']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"[📊 Open TradingView Chart]({coin['chart']})")
                st.write("")
        else:
            st.warning(f"Koi coin nahi mila jiska RSI {rsi_min}-{rsi_max} ho.")
