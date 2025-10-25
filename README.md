[![PyPI - Version](https://img.shields.io/pypi/v/btcpriceticker)](https://pypi.org/project/btcpriceticker/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/btcpriceticker)
![PyPI - Downloads](https://img.shields.io/pypi/dm/btcpriceticker)
[![codecov](https://codecov.io/gh/holgern/btcpriceticker/graph/badge.svg?token=AtcFpVooWk)](https://codecov.io/gh/holgern/btcpriceticker)

# btcpriceticker

## Overview

`btcpriceticker` is a lightweight toolkit for fetching current and historical Bitcoin
pricing data from multiple services. It powers both a handy CLI and a Python API that
can return spot prices, time series, and OHLC or OHLCV candles for BTC against your
preferred fiat currency.

## Features

- Unified interface over CoinGecko, CoinPaprika, Kraken, and mempool.space data sources
- Optional time series tracking with resampling utilities
- OHLC and OHLCV aggregation backed by pandas DataFrames
- Typer-based CLI for quick terminal access to prices, history, and candles

## Installation

```bash
pip install btcpriceticker
```

To work on the project locally:

```bash
git clone https://github.com/holgern/btcpriceticker
cd btcpriceticker
pip install -e .[test]
pip install -r requirements-test.txt  # optional extras used in this repo
```

## CLI Usage

Use the Typer-powered CLI after installation:

```bash
btcpriceticker price eur            # Show spot price in EUR
btcpriceticker history usd 1h       # Print recent hourly prices
btcpriceticker ohlc usd 1h          # Display OHLC candles
btcpriceticker ohlcv usd 1h         # Display OHLCV candles (requires services that support volume)
```

Flags such as `--service` and `--verbose` allow switching providers and log verbosity,
e.g. `btcpriceticker --service kraken price usd`.

## Python API

```python
from btcpriceticker.price import Price

price = Price(service="kraken", fiat="usd", enable_ohlcv=True)
price.refresh()

spot = price.get_price_now()
ohlcv_frame = price.ohlcv
change = price.get_price_change()
```

The `Price` object caches provider instances and exposes helper methods such as
`get_usd_price`, `get_timeseries_list`, and `set_next_service` for provider rotation.

## Testing

Run the test suite and collect coverage with:

```bash
pytest
pytest --cov=btcpriceticker
```

The project follows Ruff formatting rules and includes optional pre-commit hooks:

```bash
ruff check --fix
pre-commit run --all-files
```

## Contributing

Issues and pull requests are welcome. Please open an issue describing proposed changes
and ensure tests pass before submitting.

## License

Licensed under the MIT License. See `LICENSE` for details.
