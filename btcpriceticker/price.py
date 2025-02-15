import logging
from datetime import datetime

from .coingecko import CoinGecko
from .coinpaprika import CoinPaprika
from .mempool import Mempool
from .price_timeseries import PriceTimeSeries

logger = logging.getLogger(__name__)


class Price:
    def __init__(
        self,
        fiat="eur",
        days_ago=1,
        min_refresh_time=120,
        interval="1h",
        ohlc_interval="1h",
        service="mempool",
        enable_ohlc=False,
        enable_timeseries=True,
    ):
        self.days_ago = days_ago
        self.coingecko = CoinGecko(whichcoin="bitcoin", days_ago=days_ago)
        self.coinpaprika = CoinPaprika(whichcoin="btc-bitcoin", interval=interval)
        self.mempool = Mempool(interval=interval, days_ago=days_ago)
        if enable_ohlc:
            service = "coingecko"
        self.service = service
        self.min_refresh_time = min_refresh_time  # seconds
        self.fiat = fiat
        self.ohlc = {}
        self.price = {"usd": 0, "sat_usd": 0, "fiat": 0, "sat_fiat": 0, "timestamp": 0}
        self.enable_ohlc = enable_ohlc
        self.enable_timeseries = enable_timeseries
        self.timeseries = PriceTimeSeries()

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
            history_price = self.coingecko.get_history_price(self.fiat)
            self.timeseries.append_dataframe(history_price.data)
        now = datetime.utcnow()
        self.timeseries.add_price(now, self.price["fiat"])

    def _fetch_prices_from_coinpaprika(self):
        """Fetch prices from Coinpaprika."""
        self.price["usd"] = self.coinpaprika.get_current_price("USD")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.coinpaprika.get_current_price(self.fiat.upper())
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        if self.enable_timeseries:
            existing_timestamp = self.timeseries.get_timestamp_list()
            history_price = self.coinpaprika.get_history_price(
                existing_timestamp=existing_timestamp
            )
            self.timeseries.append_dataframe(history_price.data)
        else:
            now = datetime.utcnow()
            self.timeseries.add_price(now, self.price["fiat"])
        if self.enable_ohlc:
            self.ohlc = self.timeseries.resample_to_ohlc(self.ohlc_interval)

    def _fetch_prices_from_mempool(self):
        """Fetch prices from Mempool."""
        self.price["usd"] = self.mempool.get_current_price("USD")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.mempool.get_current_price(self.fiat.upper())
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        if self.enable_timeseries:
            existing_timestamp = self.timeseries.get_timestamp_list()
            history_price = self.mempool.get_history_price(
                self.fiat.upper(),
                existing_timestamp=existing_timestamp,
            )
            self.timeseries.append_dataframe(history_price.data)
        else:
            now = datetime.utcnow()
            self.timeseries.add_price(now, self.price["fiat"])
        if self.enable_ohlc:
            self.ohlc = self.timeseries.resample_to_ohlc(self.ohlc_interval)

    def refresh(self, service=None):
        """Refresh the price data if necessary."""
        now = datetime.utcnow()
        current_time = now.timestamp()

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
                logger.warning(f"Failed to fetch from mempool: {str(e)}")
        return False

    def get_timeseries_list(self):
        return self.timeseries.get_price_list(days=self.days_ago)

    @property
    def timeseries_stack(self):
        return self.get_timeseries_list()

    def set_days_ago(self, days_ago):
        self.coingecko.days_ago = days_ago
        self.days_ago = days_ago
        self.mempool.days_ago = days_ago

    def get_price_change(self):
        change_percentage = self.timeseries.get_percentage_change(self.days_ago)
        if not change_percentage:
            return ""
        return f"{change_percentage:+.2f}%"

    def get_fiat_price(self):
        return self.price["fiat"]

    def get_usd_price(self):
        return self.price["usd"]

    def get_sats_per_fiat(self):
        return 1e8 / self.price["fiat"]

    def get_sats_per_usd(self):
        return 1e8 / self.price["usd"]

    def get_timestamp(self):
        return self.price["timestamp"]

    def get_price_now(self):
        refresh_sucess = False
        service = self.service
        count = 0
        while not refresh_sucess and count < 3:
            service = self.get_next_service(service)
            refresh_sucess = self.refresh(service)
            count += 1

        price_now = self.price["fiat"]
        return f"{price_now:,.0f}" if price_now > 1000 else f"{price_now:.5g}"
