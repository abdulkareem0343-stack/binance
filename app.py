import pandas as pd
import ta
import ccxt
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Crypto RSI Scanner | Developed by Abdul Kareem",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Styling & Branding Logo
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e222d 0%, #131722 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2a2e39;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .app-logo {
        width: 70px;
        height: 70px;
        background: linear-gradient(135deg, #2962ff 0%, #00e676 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        box-shadow: 0 4px 15px rgba(41, 98, 255, 0.4);
    }
    .title-container {
        flex-grow: 1;
    }
    .title-text {
        color: #ffffff;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .dev-badge {
        background-color: #2962ff;
        color: #ffffff;
        font-size: 13px;
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    .rsi-badge {
        background-color: #26a69a;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2962ff 0%, #1e88e5 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 50px;
        border: none;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# App Logo Header with Developer Name
st.markdown("""
<div class="main-header">
    <div class="app-logo">⚡</div>
    <div class="title-container">
        <div class="title-text">Crypto RSI Market Scanner</div>
        <div class="dev-badge">👨‍💻 Developed by Abdul Kareem</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.header("⚙️ Scanner Settings")

timeframe = st.sidebar.selectbox("Timeframe", ["15m", "5m", "1h", "4h"], index=0)
rsi_min, rsi_max = st.sidebar.slider("RSI Range Filter", 0, 100, (30, 50))
top_gainers_count = st.sidebar.slider("Scan Top Gainers", 20, 150, 60, step=10)

# Sidebar Footer Branding
st.sidebar.markdown("---")
st.sidebar.caption("🚀 Powered by KuCoin Market Data")
st.sidebar.caption("© Created by Abdul Kareem")

# Initialize KuCoin Exchange
exchange = ccxt.kucoin({
    'enableRateLimit': True,
    'timeout': 30000,
})

def fetch_filtered_coins():
    try:
        tickers = exchange.fetch_tickers()
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        return []

    # Filter USDT Pairs & 24h Gainers
    gainers = []
    for symbol, ticker in tickers.items():
        if symbol.endswith('/USDT') and ticker.get('percentage') is not None:
            if ticker['percentage'] > 0:
                gainers.append({
                    'symbol': symbol,
                    'clean_symbol': symbol.replace('/USDT', ''),
                    'change_24h': round(ticker['percentage'], 2),
                    'price': ticker['last'],
                    'volume': round(ticker.get('quoteVolume', 0), 2)
                })
    
    gainers = sorted(gainers, key=lambda x: x['change_24h'], reverse=True)
    matching_coins = []

    status_text = st.empty()
    progress_bar = st.progress(0)
    
    scan_limit = min(len(gainers), top_gainers_count)
    
    for i, item in enumerate(gainers[:scan_limit]):
        status_text.markdown(f"🔍 **Scanning:** `{item['symbol']}` ({i+1}/{scan_limit})")
        progress_bar.progress((i + 1) / scan_limit)
        
        try:
            ohlcv = exchange.fetch_ohlcv(item['symbol'], timeframe=timeframe, limit=50)
            if not ohlcv or len(ohlcv) < 15:
                continue
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            latest_rsi = round(df['rsi'].iloc[-1], 2)
            
            # Check RSI Range Condition
            if rsi_min <= latest_rsi <= rsi_max:
                logo_symbol = item['clean_symbol'].lower()
                icon_url = f"https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/{logo_symbol}.png"
                tv_link = f"https://www.tradingview.com/chart/?symbol=KUCOIN:{item['clean_symbol']}USDT"
                
                matching_coins.append({
                    'logo': icon_url,
                    'symbol': item['clean_symbol'],
                    'full_symbol': item['symbol'],
                    'change_24h': item['change_24h'],
                    'price': item['price'],
                    'volume': f"${item['volume']:,.0f}",
                    'rsi': latest_rsi,
                    'chart_url': tv_link
                })
        except Exception:
            continue
            
    status_text.empty()
    progress_bar.empty()
    return matching_coins

# Main Scan Button
if st.button("🚀 Start Market Scan"):
    with st.spinner("Fetching Market Data & Calculating Indicators..."):
        results = fetch_filtered_coins()
        
        if results:
            st.success(f"🎯 **Found {len(results)} Token(s)** matching RSI ({rsi_min} - {rsi_max}) on {timeframe} Timeframe!")
            
            # Display Metric Summary Header
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Scanned", f"{top_gainers_count} Gainers")
            m2.metric("Matched Tokens", f"{len(results)}")
            m3.metric("Selected Timeframe", timeframe)
            
            st.divider()
            
            # Custom Table Display with Logos
            for coin in results:
                col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 2])
                
                with col1:
                    st.image(coin['logo'], width=35)
                with col2:
                    st.markdown(f"**{coin['symbol']}**")
                    st.caption("USDT")
                with col3:
                    st.markdown(f"📈 **+{coin['change_24h']}%**")
                with col4:
                    st.markdown(f"💵 **${coin['price']}**")
                with col5:
                    st.markdown(f"<span class='rsi-badge'>RSI: {coin['rsi']}</span>", unsafe_allow_html=True)
                with col6:
                    st.markdown(f"[📊 Chart]({coin['chart_url']})")
                
                st.divider()
        else:
            st.warning(f"Abhi koi aisa Gainer coin nahi mila jiska {timeframe} RSI {rsi_min} se {rsi_max} ke beech ho.")
