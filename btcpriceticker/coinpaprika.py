import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

COINPAPRIKA_MODULE = None
try:
    from coinpaprika import client as Coinpaprika

    COINPAPRIKA_MODULE = "coinpaprika"
except ImportError:
    pass


class CoinPaprika:
    def __init__(self, whichcoin="btc-bitcoin", interval="1h"):
        self.api_client = Coinpaprika.Client() if COINPAPRIKA_MODULE else None
        self.whichcoin = whichcoin
        self.interval = "1h"
        self.coins = None

    def get_coin(self, name=None, symbol=None):
        if self.coins is None:
            self.coins = self.api_client.coins()
        for coin in self.coins:
            if name and coin["name"] == name:
                return coin
            if symbol and coin["symbol"] == symbol:
                return coin
        return False

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Coinpaprika."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.ticker(self.whichcoin, quotes=currency)
            return float(ticker["quotes"][currency]["price"])
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

    def calculate_start_date(self, interval: str) -> str:
        now = datetime.utcnow()

        if interval in {"24h", "1d", "7d", "14d", "30d", "90d", "365d"}:
            start_date = now - timedelta(days=365) + timedelta(seconds=60)
        elif interval in {"1h", "2h", "3h", "6h", "12h"}:
            start_date = now - timedelta(days=1) + timedelta(seconds=60)
        else:
            raise ValueError("Invalid interval format")

        return start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    def get_history_price(self, currency):
        """Fetch historical prices from CoinPaprika."""
        logger.info(f"Getting historical data for a {self.interval} interval")
        start_date = self.calculate_start_date(self.interval)
        print(start_date)
        timeseries = self.api_client.historical(
            self.whichcoin,
            quotes=currency,
            interval=self.interval,
            start=start_date,
        )
        timeseries_stack = [float(price["price"]) for price in timeseries]
        timeseries_stack.append(self.get_current_price(currency))
        return timeseries_stack
