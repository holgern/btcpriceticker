import logging
from datetime import datetime, timedelta

import pandas as pd

from .service import Service

logger = logging.getLogger(__name__)

COINPAPRIKA_MODULE = None
try:
    from coinpaprika import client as Coinpaprika

    COINPAPRIKA_MODULE = "coinpaprika"
except ImportError:
    pass


class CoinPaprika(Service):
    def __init__(
        self,
        fiat,
        whichcoin="btc-bitcoin",
        days_ago=1,
        interval="1h",
        enable_timeseries=True,
    ):
        self.api_client = Coinpaprika.Client() if COINPAPRIKA_MODULE else None
        self.whichcoin = whichcoin
        interval = "1h"
        self.initialize(
            fiat,
            interval=interval,
            days_ago=days_ago,
            enable_timeseries=enable_timeseries,
        )
        self.coins = None
        self.name = "coinpaprika"
        self.has_ohlc = False

    def get_coin(self, name=None, symbol=None):
        if self.coins is None:
            self.coins = self.api_client.coins()
        for coin in self.coins:
            if name and coin["name"] == name:
                return coin
            if symbol and coin["symbol"] == symbol:
                return coin
        return False

    def interval_to_seconds(self) -> int:
        """Convert a time interval string to seconds."""
        unit_multipliers = {"m": 60, "h": 3600, "d": 86400}

        try:
            value, unit = int(self.interval[:-1]), self.interval[-1]
            if unit in unit_multipliers:
                return value * unit_multipliers[unit]
            else:
                raise ValueError(f"Invalid interval format {self.interval}")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid interval format {self.interval}") from e

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Coinpaprika."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.ticker(self.whichcoin, quotes=currency.upper())
            return float(ticker["quotes"][currency.upper()]["price"])
        except Exception as e:
            logger.exception(f"Failed to fetch current price: {e}")
            return None

    def get_exchange_usd_price(self, exchange, pair, currency="USD"):
        """Fetch the USD price for a given exchange and pair."""
        if not self.api_client:
            return None
        try:
            markets = self.api_client.exchange_markets(exchange, quotes=currency)
            for market in markets:
                if market["pair"] == pair:
                    return float(market["quotes"][currency]["price"])
            logger.info("Not USD, could not get price.")
            return None
        except Exception as e:
            logger.exception(f"Failed to fetch exchange USD price: {e}")
            return None

    def calculate_start_date(self, interval: str, existing_timestamp=None) -> str:
        now = datetime.utcnow()
        intervals = self.interval_to_seconds()

        if interval in {"24h", "1d", "7d", "14d", "30d", "90d", "365d"}:
            start_date = now - timedelta(days=365) + timedelta(seconds=60)
        elif interval in {"1h", "2h", "3h", "6h", "12h"}:
            start_date = now - timedelta(days=1) + timedelta(seconds=60)
        else:
            raise ValueError("Invalid interval format")

        if existing_timestamp:
            start_date_existing = datetime.utcfromtimestamp(
                existing_timestamp[-1] + 2 * intervals
            )
            if start_date < start_date_existing:
                start_date = start_date_existing

        return start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_history_price(self, currency, existing_timestamp=None):
        start_date = self.calculate_start_date(
            self.interval, existing_timestamp=existing_timestamp
        )
        timeseries = self.api_client.historical(
            self.whichcoin,
            quotes="USD",
            interval=self.interval,
            start=start_date,
        )
        return timeseries

    def update_price_history(self, currency):
        """Fetch historical prices from CoinPaprika."""
        logger.info(f"Getting historical data for a {self.interval} interval")
        existing_timestamp = self.price_history.get_timestamp_list()
        timeseries = self.get_history_price(
            currency, existing_timestamp=existing_timestamp
        )
        for price in timeseries:
            dt = datetime.strptime(price["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            self.price_history.add_price(dt, price["price"])

    def get_ohlc(self):
        start_date = self.calculate_start_date("1h", existing_timestamp=None)
        raw_ohlc = self.api_client.ohlcv(self.whichcoin, start=start_date)
        timeseries = [
            {
                "time": datetime.strptime(ohlc["time_open"], "%Y-%m-%dT%H:%M:%SZ"),
                "ohlc": [ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]],
            }
            for ohlc in raw_ohlc
            if (
                datetime.strptime(raw_ohlc[-1]["time_open"], "%Y-%m-%dT%H:%M:%SZ")
                - datetime.strptime(ohlc["time_open"], "%Y-%m-%dT%H:%M:%SZ")
            ).days
            <= self.days_ago
        ]
        return pd.DataFrame(
            [ohlc["ohlc"] for ohlc in timeseries],
            index=[ohlc["time"] for ohlc in timeseries],
            columns=["Open", "High", "Low", "Close"],
        )
