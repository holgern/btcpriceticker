import logging

import typer
from rich.console import Console

from btcpriceticker.price import Price

log = logging.getLogger(__name__)
app = typer.Typer()
console = Console()

state = {"verbose": 3}


@app.command()
def price(symbol: str):
    p = Price(
        service=state["service"],
        fiat=symbol,
        enable_timeseries=False,
        enable_ohlc=False,
    )
    p.refresh()
    price = p.get_price_now()
    print(price)


@app.command()
def history(symbol: str, interval: str):
    p = Price(
        service=state["service"],
        fiat=symbol,
        interval=interval,
        enable_timeseries=True,
        enable_ohlc=False,
    )
    p.refresh()
    print(p.timeseries.data)


@app.callback()
def main(
    verbose: int = 3,
    service: str = "mempool",
):
    """Python CLI for mempool.space, enjoy."""
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
