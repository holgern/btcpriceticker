import logging
from typing import TypedDict

import typer
from rich.console import Console

from btcpriceticker.price import Price

log = logging.getLogger(__name__)
app = typer.Typer()
console = Console()


class State(TypedDict):
    verbose: int
    service: str


state: State = {"verbose": 3, "service": "mempool"}


@app.command(help="Show the latest BTC price converted into the given fiat symbol.")
def price(
    symbol: str = typer.Argument(..., help="Fiat currency code, e.g. 'EUR'."),
    show_symbol: bool = typer.Option(
        False, help="Displays the fiat currency symbol alongside the price."
    ),
    as_float: bool = typer.Option(False, help="Returns the price as float."),
):
    p = Price(
        service=state["service"],
        fiat=symbol,
        enable_ohlc=False,
        enable_timeseries=False,
        enable_ohlcv=False,
    )
    p.refresh()
    if not as_float and show_symbol:
        price = p.get_price_now()
        symbol = p.get_fiat_symbol()
        print(f"{price} {symbol}")
    elif not as_float and not show_symbol:
        price = p.get_price_now()
        print(price)
    else:
        price = p.get_fiat_price()
        print(price)


@app.command(help="Display historical BTC prices for the requested interval.")
def history(
    symbol: str = typer.Argument(..., help="Fiat currency code, e.g. 'EUR'."),
    interval: str = typer.Argument(..., help="Sampling interval, e.g. '1h'."),
    days_ago: int = typer.Option(
        1, help="Number of days of data to pull counting back from now."
    ),
):
    p = Price(
        service=state["service"],
        days_ago=days_ago,
        fiat=symbol,
        interval=interval,
        enable_ohlc=False,
        enable_timeseries=True,
        enable_ohlcv=False,
    )
    p.refresh()
    print(p.timeseries.data)


@app.command(help="Retrieve OHLC candles converted into the requested fiat.")
def ohlc(
    symbol: str = typer.Argument(..., help="Fiat currency code, e.g. 'EUR'."),
    interval: str = typer.Argument(..., help="Candle interval, e.g. '12h'."),
    days_ago: int = typer.Option(
        1, help="Number of past days to cover when fetching candles."
    ),
):
    p = Price(
        service=state["service"],
        days_ago=days_ago,
        fiat=symbol,
        interval=interval,
        enable_ohlc=True,
        enable_timeseries=True,
        enable_ohlcv=False,
    )
    p.refresh()
    print(p.ohlc)


@app.command(help="Retrieve OHLCV candles (with synthetic volume) for BTC.")
def ohlcv(
    symbol: str = typer.Argument(..., help="Fiat currency code, e.g. 'EUR'."),
    interval: str = typer.Argument(..., help="Candle interval, e.g. '1h'."),
    days_ago: int = typer.Option(
        1, help="Number of past days to cover when fetching candles."
    ),
):
    p = Price(
        service=state["service"],
        days_ago=days_ago,
        fiat=symbol,
        interval=interval,
        enable_ohlc=False,
        enable_timeseries=True,
        enable_ohlcv=True,
    )
    p.refresh()
    print(p.ohlcv)


@app.callback()
def main(
    verbose: int = typer.Option(
        3,
        help="Verbosity level: 0=critical, 1=error, 2=warn, 3=info, 4=debug.",
    ),
    service: str = typer.Option(
        "mempool",
        help="Service backend to use, e.g. 'bit2me', 'binance', or 'mempool'.",
    ),
):
    """BTC price utilities for multiple exchange backends."""
    # Logging
    state["verbose"] = verbose
    state["service"] = service
    log = logging.getLogger(__name__)
    verbosity = ["critical", "error", "warn", "info", "debug"][int(min(verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)


if __name__ == "__main__":
    app()
