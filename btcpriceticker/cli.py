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
    p = Price(fiat=symbol, enable_timeseries=False, enable_ohlc=False)
    p.refresh()
    price = p.get_price_now()
    print(price)


if __name__ == "__main__":
    app()
