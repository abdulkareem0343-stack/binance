import pandas as pd
import ta
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
with st.expander("⚙️ Filter Options (Timeframe & RSI Range)", expanded=False):
    timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "4h"], index=0)
    rsi_min, rsi_max = st.slider("RSI Range", 0, 100, (30, 50))
    top_gainers_count = st.slider("Scan Gainers Count", 20, 400, 150, step=10)

exchange = ccxt.kucoin({'enableRateLimit': True, 'timeout': 30000})

@st.cache_data(ttl=900)
def get_binance_all_data():
    spot_assets = set()
    futures_assets = set()
    alpha_assets = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # 1. Spot Assets
    try:
        res = requests.get("https://data-api.binance.vision/api/v3/exchangeInfo", headers=headers, timeout=10)
        data = res.json()
        for s in data.get('symbols', []):
            if s.get('status') == 'TRADING' and s['symbol'].endswith('USDT'):
                spot_assets.add(s['baseAsset'].upper())
    except Exception:
        pass

    # 2. Futures Assets
    try:
        res_f = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", headers=headers, timeout=10)
        data_f = res_f.json()
        for s in data_f.get('symbols', []):
            if s.get('status') == 'TRADING' and s['symbol'].endswith('USDT'):
                futures_assets.add(s['baseAsset'].upper())
    except Exception:
        pass

    # 3. Binance Web3 & Alpha List Direct Source
    try:
        url_alpha = "https://www.binance.com/bapi/composite/v1/public/promo/cmc/alpha/token/list"
        res_a = requests.get(url_alpha, headers=headers, timeout=10)
        if res_a.status_code == 200:
            tokens = res_a.json().get('data', [])
            for t in tokens:
                sym = t.get('symbol', '').upper()
                if sym:
                    alpha_assets.add(sym)
    except Exception:
        pass

    # 4. Futures Tickers Fallback for Alpha
    try:
        res_af = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr", headers=headers, timeout=10)
        if res_af.status_code == 200:
            for item in res_af.json():
                s = item.get('symbol', '').upper()
                if s.endswith('USDT'):
                    alpha_assets.add(s.replace('USDT', ''))
    except Exception:
        pass

    # Complete Expanded Binance Alpha/Early Zone Tokens Base
    known_alpha = {
        "4STOCK", "RIZ", "NOCH", "ASTER", "MEMECORE", "MORPHO", "VENICE", "STABLE", 
        "SPX", "VIRTUAL", "CHEEMS", "BUILDON", "FARTCOIN", "BULLA", "PONS", "CAP", 
        "UAI", "SLX", "HIGH", "PHA", "SWARM", "PENGU", "GRASS", "DRIFT", "EIGEN", 
        "TURBO", "NEIRO", "BABYDOGE", "CATI", "HMSTR", "1000SATS", "SATS"
    }
    alpha_assets.update(known_alpha)

    return spot_assets, futures_assets, alpha_assets

def fetch_filtered_coins():
    spot_assets, futures_assets, alpha_assets = get_binance_all_data()

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
                    'clean_symbol': symbol.replace('/USDT', '').upper(),
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
                
                coin_code = item['clean_symbol']
                
                is_spot = coin_code in spot_assets
                is_futures = coin_code in futures_assets
                
                # Check directly in Alpha pool, or if token is on Futures but not Spot
                is_alpha = (coin_code in alpha_assets) or (is_futures and not is_spot)
                
                matching_coins.append({
                    'symbol': coin_code,
                    'change_24h': item['change_24h'],
                    'price': item['price'],
                    'rsi': latest_rsi,
                    'chart': tv_link,
                    'is_spot': is_spot,
                    'is_futures': is_futures,
                    'is_alpha': is_alpha
                })
        except Exception:
            continue
            
    status.empty()
    progress.empty()
    
    matching_coins = sorted(matching_coins, key=lambda x: x['rsi'])
    return matching_coins

# Main Mobile Scan Trigger Button
if st.button("🚀 Start App Scan"):
    with st.spinner("Scanning Market..."):
        results = fetch_filtered_coins()
        
        if results:
            st.caption(f"Found {len(results)} Token(s) | Sorted Low to High RSI")
            
            for coin in results:
                spot_tag = '<span class="spot-badge">BINANCE SPOT</span>' if coin['is_spot'] else ''
                futures_tag = '<span class="futures-badge">FUTURES</span>' if coin['is_futures'] else ''
                alpha_tag = '<span class="alpha-badge">BINANCE ALPHA</span>' if coin['is_alpha'] else ''
                
                st.markdown(f"""
                <div class="coin-card">
                    <div class="card-top">
                        <span class="symbol-title">
                            🪙 {coin['symbol']}/USDT {spot_tag} {futures_tag} {alpha_tag}
                        </span>
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
