import logging
from datetime import datetime

import pandas as pd
from pycoingecko import CoinGeckoAPI

from .service import Service

logger = logging.getLogger(__name__)


class CoinGecko(Service):
    def __init__(
        self,
        fiat,
        whichcoin="bitcoin",
        days_ago=1,
        enable_timeseries=True,
        enable_ohlc=True,
    ):
        self.cg = CoinGeckoAPI()
        self.whichcoin = whichcoin
        self.initialize(
            fiat,
            days_ago=days_ago,
            enable_timeseries=enable_timeseries,
            enable_ohlc=enable_ohlc,
        )
        self.name = "coingecko"
        self.has_ohlc = True

    def get_current_price(self, currency):
        """Fetch the current price for the given currency from CoinGecko."""
        try:
            return float(
                self.cg.get_coins_markets(currency, ids=self.whichcoin)[0][
                    "current_price"
                ]
            )
        except (IndexError, KeyError):
            logger.error(f"Failed to retrieve price for {self.whichcoin} in {currency}")
            return None

    def get_exchange_usd_price(self, exchange):
        """Fetch the USD price for the given exchange."""
        try:
            raw_data = self.cg.get_exchanges_tickers_by_id(
                exchange, coin_ids=self.whichcoin
            )
            ticker = raw_data["tickers"][0]
            if ticker["target"] != "USD":
                logger.info("Not USD, could not get price.")
                return None
            return float(ticker["last"])
        except (IndexError, KeyError):
            logger.error(f"Failed to retrieve exchange price for {exchange}")
            return None

    def interval_to_seconds(self) -> int:
        return 60 * 5

    def get_history_price(self, currency, existing_timestamp=None):
        if existing_timestamp:
            now = datetime.utcnow()
            intervals = self.interval_to_seconds()
            start_time = datetime.utcfromtimestamp(existing_timestamp[-1] + intervals)
            raw_data = self.cg.get_coin_market_chart_range_by_id(
                self.whichcoin,
                currency,
                from_timestamp=start_time.timestamp(),
                to_timestamp=now.timestamp(),
            )
        else:
            raw_data = self.cg.get_coin_market_chart_by_id(
                self.whichcoin, currency, self.days_ago
            )
        return raw_data

    def update_price_history(self, currency):
        """Fetch historical prices from CoinGecko."""
        logger.info(f"Getting historical data for {self.days_ago} days")
        existing_timestamp = self.price_history.get_timestamp_list()
        raw_data = self.get_history_price(
            currency, existing_timestamp=existing_timestamp
        )
        timeseries = raw_data.get("prices", [])
        for price in timeseries:
            dt = datetime.fromtimestamp(float(price[0]) / 1000)
            self.price_history.add_price(dt, float(price[1]))

    def get_ohlc(self, currency):
        """Fetch OHLC data based on the number of days ago."""
        time_ranges = [1, 7, 14, 30, 90, 180, 365]
        duration = next((d for d in time_ranges if self.days_ago <= d), "max")
        raw_ohlc = self.cg.get_coin_ohlc_by_id(self.whichcoin, currency, duration)

        timeseries = [
            {"time": datetime.utcfromtimestamp(ohlc[0] / 1000), "ohlc": ohlc[1:]}
            for ohlc in raw_ohlc
            if (
                datetime.utcfromtimestamp(raw_ohlc[-1][0] / 1000)
                - datetime.utcfromtimestamp(ohlc[0] / 1000)
            ).days
            <= self.days_ago
        ]
        return pd.DataFrame(
            [ohlc["ohlc"] for ohlc in timeseries],
            index=[ohlc["time"] for ohlc in timeseries],
            columns=["Open", "High", "Low", "Close"],
        )
