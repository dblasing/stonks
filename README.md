# stonks

Quick CLI for plotting stock price history with a simple moving average and
annotated local peaks and troughs. Backed by [yfinance](https://pypi.org/project/yfinance/)
for prices and [scipy.signal.argrelextrema](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.argrelextrema.html)
for the extrema detection.

## Install

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```sh
# Single ticker, defaults (365 days, 50-day SMA)
./stonks.py PLTR

# Custom window
./stonks.py NVDA --days 180 --sma 30

# Multiple tickers — opens one chart per ticker
./stonks.py PLTR NVDA TSLA

# Save to PNG instead of showing interactively
./stonks.py PLTR --out pltr.png

# With multiple tickers and --out, ticker is appended:
#   chart_PLTR.png, chart_NVDA.png, chart_TSLA.png
./stonks.py PLTR NVDA TSLA --out chart.png
```

### Tuning the peak/trough detection

`--order N` controls how strict `argrelextrema` is — a peak must be greater
than `N` neighbors on each side to qualify. Higher values surface fewer, more
significant turning points; lower values surface more noise.

```sh
./stonks.py PLTR --order 12   # only the biggest swings
./stonks.py PLTR --order 3    # every wiggle
```

## Notes

Prices are auto-adjusted (splits and dividends) by yfinance. Strict
`np.greater` / `np.less` are used so flat plateaus do not register as
extrema.
