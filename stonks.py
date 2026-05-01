#!/usr/bin/env python3
"""
stonks — quick stock chart tool.

Fetches daily price history for one or more tickers, overlays a simple moving
average, and annotates local peaks (green) and troughs (red) using
scipy.signal.argrelextrema.

Usage:
    ./stonks.py PLTR
    ./stonks.py PLTR NVDA TSLA --days 180 --sma 30
    ./stonks.py PLTR --out chart.png
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.signal import argrelextrema

# --- Defaults ------------------------------------------------------------
DEFAULT_DAYS = 365
DEFAULT_SMA_WINDOW = 50
# argrelextrema "order" = number of points on each side that must be smaller
# (for peaks) for a point to qualify. Higher = fewer, more significant peaks.
DEFAULT_EXTREMA_ORDER = 7


def fetch_prices(ticker: str, days: int) -> pd.DataFrame:
    """Download adjusted daily prices for `ticker` over the last `days` days."""
    end = datetime.now()
    start = end - timedelta(days=days)
    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=True,
    )
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    return df


def add_sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Return a copy of `df` with a simple moving average column added."""
    df = df.copy()
    df[f"MA{window}"] = df["Close"].rolling(window=window).mean()
    return df


def find_extrema(closes: np.ndarray, order: int):
    """Return (peak_indices, trough_indices) for a 1D array of closing prices.

    Uses strict greater/less rather than >=, <= so that flat plateaus do not
    register as peaks or troughs.
    """
    closes = np.asarray(closes).flatten()
    high_idx = argrelextrema(closes, np.greater, order=order)[0]
    low_idx = argrelextrema(closes, np.less, order=order)[0]
    return high_idx, low_idx


def plot_chart(
    df: pd.DataFrame,
    ticker: str,
    sma_window: int,
    high_idx: np.ndarray,
    low_idx: np.ndarray,
    out: Path | None = None,
) -> None:
    """Render the price chart with SMA and annotated extrema."""
    fig, ax = plt.subplots(figsize=(16, 8))

    ax.plot(
        df.index,
        df["Close"],
        label="Close Price",
        color="tab:blue",
        linewidth=1.5,
        zorder=1,
    )
    sma_col = f"MA{sma_window}"
    ax.plot(
        df.index,
        df[sma_col],
        label=f"{sma_window}-day SMA",
        color="tab:orange",
        linewidth=2.5,
        zorder=1,
    )

    _annotate_points(ax, df, high_idx, color="green", offset=25, label_color="darkgreen", bg="lightgreen")
    _annotate_points(ax, df, low_idx,  color="red",   offset=-28, label_color="darkred",   bg="lightcoral", va="top")

    ax.set_title(
        f"{ticker} — {len(df)}-bar Price + {sma_window}-day SMA\n"
        f"(Local Peaks in Green • Local Troughs in Red)",
        fontsize=16,
        pad=30,
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend()
    ax.grid(alpha=0.3)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    if out is not None:
        plt.savefig(out, dpi=120)
        print(f"  saved chart to {out}")
        plt.close(fig)
    else:
        plt.show()


def _annotate_points(ax, df, idx, *, color, offset, label_color, bg, va="bottom"):
    """Helper: scatter + price label for each index in `idx`."""
    for i in idx:
        date = df.index[i]
        price = float(df["Close"].iloc[i])
        ax.scatter(date, price, color=color, s=250, zorder=5,
                   edgecolor="black", linewidth=1.5)
        ax.annotate(
            f"{price:.2f}",
            xy=(date, price),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=11,
            fontweight="bold",
            color=label_color,
            bbox=dict(boxstyle="round,pad=0.5", fc=bg, alpha=0.9),
            zorder=6,
        )


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plot stock price with SMA and local extrema."
    )
    p.add_argument("tickers", nargs="+",
                   help="Ticker symbols (e.g. PLTR NVDA TSLA)")
    p.add_argument("--days", type=int, default=DEFAULT_DAYS,
                   help=f"Lookback window in days (default {DEFAULT_DAYS})")
    p.add_argument("--sma", type=int, default=DEFAULT_SMA_WINDOW,
                   help=f"SMA window in days (default {DEFAULT_SMA_WINDOW})")
    p.add_argument("--order", type=int, default=DEFAULT_EXTREMA_ORDER,
                   help=("argrelextrema order — higher = fewer/larger peaks "
                         f"(default {DEFAULT_EXTREMA_ORDER})"))
    p.add_argument("--out", type=Path, default=None,
                   help="Save chart to file instead of showing interactively. "
                        "With multiple tickers, the ticker is appended to the stem.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    for ticker in args.tickers:
        ticker = ticker.upper()
        print(f"Fetching {ticker} ({args.days}d)...")
        try:
            df = fetch_prices(ticker, args.days)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue

        df = add_sma(df, args.sma)
        high_idx, low_idx = find_extrema(df["Close"].to_numpy(), args.order)
        print(f"  {len(high_idx)} peaks, {len(low_idx)} troughs")

        out = args.out
        if out is not None and len(args.tickers) > 1:
            out = out.with_stem(f"{out.stem}_{ticker}")

        plot_chart(df, ticker, args.sma, high_idx, low_idx, out=out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
