import yfinance as yf
import akshare as ak
import pandas as pd
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
    # data = yf.download(symbol, period="1y")["Close"]
    data = ak.stock_us_daily(symbol=symbol, adjust='qfq')['close']

    window = dynamic_window(data, base_window)

    rolling_high = data.rolling(window).max()

    price = data.iloc[-1]
    high = rolling_high.iloc[-1]

    dd = (price - high) / high

    ma200 = data.rolling(200).mean().iloc[-1]
    uptrend = price > ma200

    # scoring
    score = 0
    if uptrend:
        score += 1
    if dd <= -0.10:
        score += 1
    if dd <= -0.15:
        score += 2
    if dd <= -0.20:
        score += 3

    return {
        "symbol": symbol,
        "price": price,
        "high": high,
        "dd": dd,
        "window": window,
        "score": score,
        "trend": uptrend
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