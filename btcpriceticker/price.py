import logging
import time

from .coingecko import CoinGecko
from .coinpaprika import CoinPaprika
from .mempool import Mempool

logger = logging.getLogger(__name__)


class Price:
    def __init__(
        self,
        fiat="eur",
        days_ago=1,
        service="coingecko",
        enable_ohlc=True,
        enable_timeseries=True,
    ):
        self.coingecko = CoinGecko(whichcoin="bitcoin", days_ago=days_ago)
        self.coinpaprika = CoinPaprika(whichcoin="btc-bitcoin")
        self.mempool = Mempool()
        self.service = service
        self.min_refresh_time = 120  # seconds
        self.fiat = fiat
        self.ohlc = {}
        self.price = {}
        self.enable_ohlc = enable_ohlc
        self.enable_timeseries = enable_timeseries
        self.timeseries_stack = []

    def get_next_service(self, service):
        if service == "coingecko":
            return "coinpaprika"
        elif service == "coinpaprika":
            return "mempool"
        elif service == "mempool":
            return "coingecko"

    def _fetch_prices_from_coingecko(self):
        """Fetch prices and OHLC data from CoinGecko."""
        self.price["usd"] = self.coingecko.get_current_price("usd")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.coingecko.get_current_price(self.fiat)
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        if self.enable_ohlc:
            self.ohlc = self.coingecko.get_ohlc(self.fiat)
        if self.enable_timeseries:
            self.timeseries_stack = self.coingecko.get_history_price(self.fiat)
        else:
            self.timeseries_stack = [self.price["fiat"]]

    def _fetch_prices_from_coinpaprika(self):
        """Fetch prices from Coinpaprika."""
        self.price["usd"] = self.coinpaprika.get_current_price("USD")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.coinpaprika.get_current_price(self.fiat.upper())
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        self.timeseries_stack = [self.price["fiat"]]
        self.ohlc = {}

    def _fetch_prices_from_mempool(self):
        """Fetch prices from Mempool."""
        self.price["usd"] = self.mempool.get_current_price("USD")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.mempool.get_current_price(self.fiat.upper())
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        self.timeseries_stack = [self.price["fiat"]]
        self.ohlc = {}

    def refresh(self, service=None):
        """Refresh the price data if necessary."""
        current_time = time.time()

        if (
            "timestamp" in self.price
            and current_time - self.price["timestamp"] < self.min_refresh_time
        ):
            return True

        logger.info("Fetching price data...")
        if service is None:
            service = self.service
        self.price = {}
        if self.service == "coingecko":
            try:
                self._fetch_prices_from_coingecko()
                self.price["timestamp"] = current_time
                return True
            except Exception as e:
                logger.warning(f"Failed to fetch from CoinGecko: {str(e)}")
        elif self.service == "coinpaprika":
            try:
                self._fetch_prices_from_coinpaprika()
                self.price["timestamp"] = current_time
                return True
            except Exception as e:
                logger.warning(f"Failed to fetch from CoinPaprika: {str(e)}")
        else:
            try:
                self._fetch_prices_from_mempool()
                self.price["timestamp"] = current_time
                return True
            except Exception as e:
                logger.warning(f"Failed to fetch from CoinPaprika: {str(e)}")
        return False

    def set_days_ago(self, days_ago):
        self.coingecko.days_ago = days_ago

    @property
    def days_ago(self):
        return self.coingecko.days_ago

    def get_price_change(self):
        if len(self.timeseries_stack) < 2:
            return ""

        change_percentage = (
            (self.timeseries_stack[-1] - self.timeseries_stack[0])
            / self.timeseries_stack[0]
        ) * 100
        return f"{change_percentage:+.2f}%"

    def get_price_now(self):
        refresh_sucess = False
        service = self.service
        count = 0
        while not refresh_sucess and count < 3:
            service = self.get_next_service(service)
            refresh_sucess = self.refresh(service)
            count += 1

        if not self.timeseries_stack:
            return self.price["fiat"]

        price_now = self.timeseries_stack[-1]
        return f"{price_now:,.0f}" if price_now > 1000 else f"{price_now:.5g}"
