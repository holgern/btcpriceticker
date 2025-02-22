import logging
from datetime import datetime, timedelta

import pandas as pd

from .service import Service

logger = logging.getLogger(__name__)

MEMPOOL_MODULE = None
try:
    from pymempool.api import MempoolAPI

    MEMPOOL_MODULE = "pymempool"
except ImportError:
    pass


class Mempool(Service):
    def __init__(
        self,
        fiat,
        interval="1h",
        days_ago=1,
        enable_timeseries=False,
    ):
        self.api_client = MempoolAPI() if MEMPOOL_MODULE else None
        self.initialize(
            fiat,
            interval=interval,
            days_ago=days_ago,
            enable_ohlc=False,
            enable_timeseries=enable_timeseries,
        )
        self.name = "mempool"
        self.has_ohlc = False

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Mempool."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.get_price()
            return float(ticker[currency.upper()])
        except Exception as e:
            logger.exception(f"Failed to fetch current price: {e}")
            return None

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

    def calculate_start_date(self):
        now = datetime.utcnow()
        return now - timedelta(days=self.days_ago)

    def calculate_time_vector(self, existing_timestamp=None):
        """Generate timestamps based on the interval."""
        now = datetime.utcnow()
        intervals = self.interval_to_seconds()

        if not existing_timestamp:
            start_time = self.calculate_start_date()
        else:
            start_time = datetime.utcfromtimestamp(
                existing_timestamp[-1] + 2 * intervals
            )
        time_vector = list(
            range(
                int(start_time.timestamp()),
                int(now.timestamp()),
                intervals,
            )
        )

        return time_vector

    def get_history_price(self, currency, existing_timestamp=None):
        history_prices = []
        time_vector = self.calculate_time_vector(existing_timestamp=existing_timestamp)
        for timestamp in time_vector:
            price = self.api_client.get_historical_price(
                currency=currency.upper(), timestamp=timestamp
            )
            price_value = float(price["prices"][0][currency.upper()])
            history_prices.append((datetime.fromtimestamp(timestamp), price_value))
        return history_prices

    def update_price_history(self, currency):
        """Fetch historical prices from Mempool."""
        logger.info(f"Getting historical data for a {self.interval} interval")
        existing_timestamp = self.price_history.get_timestamp_list()
        history_prices = self.get_history_price(
            currency, existing_timestamp=existing_timestamp
        )
        for price_time, price_value in history_prices:
            self.price_history.add_price(price_time, price_value)

    def get_ohlc(self):
        return pd.DataFrame(
            [],
            index=[],
            columns=["Open", "High", "Low", "Close"],
        )
