import pandas as pd
import ccxt
import requests
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 500px !important;
    }
    
    body {
        background-color: #121212;
        color: #e0e0e0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

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
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }
    .gainer-tag {
        background-color: rgba(0, 200, 83, 0.15);
        color: #00e676;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
    }
    .loser-tag {
        background-color: rgba(255, 23, 68, 0.15);
        color: #ff1744;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
    }
    .spot-badge {
        background-color: #F0B90B;
        color: #000000;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .futures-badge {
        background-color: #9c27b0;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .alpha-badge {
        background-color: #00e5ff;
        color: #000000;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .card-bottom {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .price-text {
        font-size: 15px;
        font-weight: 600;
        color: #b0bec5;
    }
    .rsi-container {
        display: flex;
        gap: 6px;
    }
    .rsi-badge {
        background: linear-gradient(135deg, #2962ff 0%, #00b0ff 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
    }
    .rsi200-badge {
        background: linear-gradient(135deg, #7b1fa2 0%, #e040fb 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
    }
    .chart-btn {
        display: block;
        text-align: center;
        background: #2a2a2a;
        color: #2962ff !important;
        text-decoration: none;
        padding: 8px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #3a3a3a;
    }
    
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

# Controls
with st.expander("⚙️ Filter Options (Gain/Loss & RSI)", expanded=True):
    scan_type = st.radio("Market Filter", ["🚀 Top Gainers", "📉 Top Losers"], horizontal=True)
    timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "4h"], index=0)
    
    # RSI 14 Range
    rsi14_min, rsi14_max = st.slider("RSI (14) Range", 0, 100, (30, 50))
    
    # RSI 200 Range
    rsi200_min, rsi200_max = st.slider("RSI (200) Range", 0, 100, (30, 70))
    
    top_coins_count = st.slider("Scan Coins Count", 20, 400, 150, step=10)

# KuCoin Exchange Integration
exchange = ccxt.kucoin({'enableRateLimit': True, 'timeout': 30000})

# Generic Wilder's RSI Formula
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

@st.cache_data(ttl=900)
def get_binance_all_data():
    spot_assets = set()
    futures_assets = set()
    alpha_assets = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # Fetch Binance Spot Assets
    for url in ["https://api.binance.com/api/v3/exchangeInfo", "https://data-api.binance.vision/api/v3/exchangeInfo"]:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                for s in data.get('symbols', []):
                    if s.get('status') == 'TRADING' and s.get('symbol', '').endswith('USDT'):
                        spot_assets.add(s.get('baseAsset', '').upper())
                break
        except Exception:
            continue

    # Fetch Binance Futures Assets
    try:
        res_f = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", headers=headers, timeout=8)
        if res_f.status_code == 200:
            data_f = res_f.json()
            for s in data_f.get('symbols', []):
                if s.get('status') == 'TRADING' and s.get('symbol', '').endswith('USDT'):
                    base = s.get('baseAsset', '').upper()
                    futures_assets.add(base)
                    clean_base = base.replace('1000000', '').replace('1000', '')
                    futures_assets.add(clean_base)
    except Exception:
        pass

    # Binance Alpha Assets
    try:
        url_alpha = "https://www.binance.com/bapi/composite/v1/public/promo/cmc/alpha/token/list"
        res_a = requests.get(url_alpha, headers=headers, timeout=8)
        if res_a.status_code == 200:
            tokens = res_a.json().get('data', [])
            for t in tokens:
                sym = t.get('symbol', '').upper()
                if sym:
                    alpha_assets.add(sym)
    except Exception:
        pass

    known_alpha = {
        "4STOCK", "RIZ", "NOCH", "ASTER", "MEMECORE", "MORPHO", "VENICE", "STABLE", 
        "SPX", "VIRTUAL", "CHEEMS", "BUILDON", "FARTCOIN", "BULLA", "PONS", "CAP", 
        "UAI", "SLX", "HIGH", "PHA", "SWARM", "PENGU", "GRASS", "DRIFT", "EIGEN", 
        "TURBO", "NEIRO", "BABYDOGE", "CATI", "HMSTR", "1000SATS", "SATS"
    }
    alpha_assets.update(known_alpha)

    return spot_assets, futures_assets, alpha_assets

def fetch_filtered_coins(is_gainer_mode=True):
    spot_assets, futures_assets, alpha_assets = get_binance_all_data()

    try:
        tickers = exchange.fetch_tickers()
    except Exception as e:
        st.error(f"Error connecting to KuCoin: {e}")
        return []

    selected_pool = []
    for symbol, ticker in tickers.items():
        if symbol.endswith('/USDT') and ticker.get('percentage') is not None:
            pct = ticker['percentage']
            # Gainers Mode: pct > 0 | Losers Mode: pct < 0
            if is_gainer_mode and pct > 0:
                selected_pool.append({
                    'symbol': symbol,
                    'clean_symbol': symbol.replace('/USDT', '').upper(),
                    'change_24h': round(pct, 2),
                    'price': ticker['last']
                })
            elif not is_gainer_mode and pct < 0:
                selected_pool.append({
                    'symbol': symbol,
                    'clean_symbol': symbol.replace('/USDT', '').upper(),
                    'change_24h': round(pct, 2),
                    'price': ticker['last']
                })
    
    # Sort top gainers (highest positive) or top losers (most negative)
    if is_gainer_mode:
        selected_pool = sorted(selected_pool, key=lambda x: x['change_24h'], reverse=True)
    else:
        selected_pool = sorted(selected_pool, key=lambda x: x['change_24h'])

    matching_coins = []

    status = st.empty()
    progress = st.progress(0)
    limit = min(len(selected_pool), top_coins_count)

    for i, item in enumerate(selected_pool[:limit]):
        status.caption(f"Scanning KuCoin {item['clean_symbol']} ({i+1}/{limit})...")
        progress.progress((i + 1) / limit)
        
        try:
            # Fetching 350 candles so RSI(200) has enough historical data to calculate accurately
            ohlcv = exchange.fetch_ohlcv(item['symbol'], timeframe=timeframe, limit=350)
            if not ohlcv or len(ohlcv) < 205:
                continue
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            latest_rsi14 = calculate_rsi(df['close'], period=14)
            latest_rsi200 = calculate_rsi(df['close'], period=200)
            
            # Check if both RSI 14 and RSI 200 fall inside selected ranges
            if (rsi14_min <= latest_rsi14 <= rsi14_max) and (rsi200_min <= latest_rsi200 <= rsi200_max):
                tv_link = f"https://www.tradingview.com/chart/?symbol=KUCOIN:{item['clean_symbol']}USDT"
                
                coin_code = item['clean_symbol']
                is_spot = coin_code in spot_assets
                is_futures = coin_code in futures_assets
                is_alpha = coin_code in alpha_assets

                badges_html = ""
                if is_spot:
                    badges_html += '<span class="spot-badge">SPOT</span> '
                if is_futures:
                    badges_html += '<span class="futures-badge">FUTURES</span> '
                if is_alpha:
                    badges_html += '<span class="alpha-badge">ALPHA</span> '

                change_class = "gainer-tag" if item['change_24h'] >= 0 else "loser-tag"
                change_sign = "+" if item['change_24h'] >= 0 else ""

                card_html = f"""
                <div class="coin-card">
                    <div class="card-top">
                        <div class="symbol-title">
                            {item['clean_symbol']}
                            {badges_html}
                        </div>
                        <div class="{change_class}">
                            {change_sign}{item['change_24h']}%
                        </div>
                    </div>
                    <div class="card-bottom">
                        <div class="price-text">${item['price']}</div>
                        <div class="rsi-container">
                            <div class="rsi-badge">RSI14: {latest_rsi14}</div>
                            <div class="rsi200-badge">RSI200: {latest_rsi200}</div>
                        </div>
                    </div>
                    <a href="{tv_link}" target="_blank" class="chart-btn">📈 Open Chart</a>
                </div>
                """
                matching_coins.append(card_html)
        except Exception:
            continue

    status.empty()
    progress.empty()
    return matching_coins

# Main Trigger Button
is_gainer = (scan_type == "🚀 Top Gainers")
if st.button("🔍 Run Crypto Scan"):
    results = fetch_filtered_coins(is_gainer_mode=is_gainer)
    if results:
        st.success(f"Found {len(results)} matching coins!")
        for card in results:
            st.markdown(card, unsafe_allow_html=True)
    else:
        st.warning("No coins found matching your criteria. Try adjusting the RSI ranges or timeframe.")
