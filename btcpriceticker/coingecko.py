import logging
from datetime import datetime

import pandas as pd
from pycoingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)


class CoinGecko:
    def __init__(self, whichcoin="bitcoin", days_ago=1):
        self.cg = CoinGeckoAPI()
        self.whichcoin = whichcoin
        self.days_ago = days_ago

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

    def get_history_price(self, currency):
        """Fetch historical prices from CoinGecko."""
        logger.info(f"Getting historical data for {self.days_ago} days")
        raw_data = self.cg.get_coin_market_chart_by_id(
            self.whichcoin, currency, self.days_ago
        )
        timeseries = raw_data.get("prices", [])
        timeseries_stack = [float(price[1]) for price in timeseries]
        timeseries_stack.append(self.get_current_price(currency))
        return timeseries_stack

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
