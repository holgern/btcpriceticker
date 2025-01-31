import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MEMPOOL_MODULE = None
try:
    from pymempool.api import MempoolAPI

    MEMPOOL_MODULE = "pymempool"
except ImportError:
    pass


class Mempool:
    def __init__(self, interval="1h", days_ago=1):
        self.api_client = MempoolAPI() if MEMPOOL_MODULE else None
        self.interval = interval
        self.days_ago = days_ago

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Mempool."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.get_price()
            return float(ticker[currency])
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
                raise ValueError("Invalid interval format")
        except (ValueError, IndexError) as e:
            raise ValueError("Invalid interval format") from e

    def calculate_start_date(self):
        now = datetime.utcnow()
        return now - timedelta(days=self.days_ago)

    def calculate_time_vector(self):
        """Generate timestamps based on the interval."""
        now = datetime.utcnow()

        start_time = self.calculate_start_date()
        intervals = self.interval_to_seconds()
        time_vector = list(
            range(
                int(start_time.timestamp()),
                int(now.timestamp()),
                intervals,
            )
        )
        return time_vector

    def get_history_price(self, currency):
        """Fetch historical prices from Mempool."""
        logger.info(f"Getting historical data for a {self.interval} interval")
        time_vector = self.calculate_time_vector()
        timeseries_stack = []
        for timestamp in time_vector:
            price = self.api_client.get_historical_price(
                currency=currency, timestamp=timestamp
            )

            timeseries_stack.append(float(price["prices"][0][currency]))
        timeseries_stack.append(self.get_current_price(currency))
        return timeseries_stack
