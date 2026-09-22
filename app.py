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
            fetch_limit = 350 if use_rsi200 else 100
            ohlcv = exchange.fetch_ohlcv(item['symbol'], timeframe=timeframe, limit=fetch_limit)
            
            min_candles_required = 205 if use_rsi200 else 30
            if not ohlcv or len(ohlcv) < min_candles_required:
                continue
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            rsi14_passed = True
            latest_rsi14 = calculate_rsi(df['close'], period=14)
            if use_rsi14:
                rsi14_passed = (rsi14_min <= latest_rsi14 <= rsi14_max)

            rsi200_passed = True
            latest_rsi200 = None
            if use_rsi200:
                latest_rsi200 = calculate_rsi(df['close'], period=200)
                rsi200_passed = (rsi200_min <= latest_rsi200 <= rsi200_max)

            if rsi14_passed and rsi200_passed:
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

                rsi_badges_html = f'<div class="rsi-badge">RSI14: {latest_rsi14}</div>'
                if latest_rsi200 is not None:
                    rsi_badges_html += f'<div class="rsi200-badge">RSI200: {latest_rsi200}</div>'

                card_html = (
                    f'<div class="coin-card">'
                    f'  <div class="card-top">'
                    f'    <div class="symbol-title">{item["clean_symbol"]} {badges_html}</div>'
                    f'    <div class="{change_class}">{change_sign}{item["change_24h"]}%</div>'
                    f'  </div>'
                    f'  <div class="card-bottom">'
                    f'    <div class="price-text">${item["price"]}</div>'
                    f'    <div class="rsi-container">{rsi_badges_html}</div>'
                    f'  </div>'
                    f'  <a href="{tv_link}" target="_blank" class="chart-btn">📈 Open Chart</a>'
                    f'</div>'
                )
                
                # Store object with rsi14_val for sorting
                matching_coins.append({
                    'rsi14_val': latest_rsi14,
                    'card_html': card_html
                })
        except Exception:
            continue

    status.empty()
    progress.empty()
    
    # Sort matching coins by RSI 14 (lowest to highest)
    matching_coins = sorted(matching_coins, key=lambda x: x['rsi14_val'])
    
    # Extract only HTML cards
    return [coin['card_html'] for coin in matching_coins]
