import yfinance as yf
import numpy as np
from config import ETFS, TARGET_VOL
from notifier import send_telegram


def dynamic_window(data, base_window):
    returns = data.pct_change().dropna()
    vol = returns.std() * np.sqrt(252)

    if vol == 0 or np.isnan(vol):
        return base_window

    window = int(base_window * (TARGET_VOL / vol))
    return max(20, min(window, 120))


def analyze(symbol, base_window):
    print(f"\n🔍 Fetching {symbol}")

    data = yf.download(symbol, period="1y")

    if data.empty:
        print(f"❌ {symbol} data empty")
        return None

    close = data["Close"]

    # ===== 动态 window =====
    returns = close.pct_change().dropna()
    vol = returns.std() * np.sqrt(252)

    if vol == 0 or np.isnan(vol):
        window = base_window
    else:
        window = int(base_window * (0.2 / vol))
        window = max(20, min(window, 120))

    # ===== rolling high =====
    rolling_high = close.rolling(window).max()

    # ❗关键：全部取最后一个值
    price = close.iloc[-1]
    high = rolling_high.iloc[-1]

    if np.isnan(high) or high == 0:
        print(f"❌ {symbol} invalid high")
        return None

    dd = (price - high) / high

    # ===== 趋势 =====
    ma200 = close.rolling(200).mean().iloc[-1]
    uptrend = price > ma200

    # ===== 状态（全部是标量）=====
    if dd <= -0.20 and uptrend:
        state = "DEEP"
    elif dd <= -0.15 and uptrend:
        state = "BUY"
    elif dd <= -0.10 and uptrend:
        state = "WATCH"
    else:
        state = "NO"

    return {
        "symbol": symbol,
        "price": price,
        "high": high,
        "dd": dd,
        "window": window,
        "trend": uptrend,
        "state": state
    }


def build_message(results):
    msg = "📊 *ETF Quant Signals*\n\n"

    for r in results:
        state = (
            "🚀 DEEP" if r["score"] >= 4 else
            "🟢 BUY" if r["score"] >= 3 else
            "🟡 WATCH" if r["score"] >= 2 else
            "⚪ NO TRADE"
        )

        msg += (
            f"*{r['symbol']}*\n"
            f"Price: {r['price']:.2f}\n"
            f"High: {r['high']:.2f}\n"
            f"DD: {r['dd']:.2%}\n"
            f"Window: {r['window']}\n"
            f"Trend: {'UP' if r['trend'] else 'DOWN'}\n"
            f"{state}\n\n"
        )

    return msg


def run():
    results = []

    for s, w in ETFS.items():
        try:
            r = analyze(s, w)
            results.append(r)
        except Exception as e:
            print(f"{s} error:", e)

    results.sort(key=lambda x: x["score"], reverse=True)

    msg = build_message(results)

    print(msg)
    send_telegram(msg)


if __name__ == "__main__":
    run()