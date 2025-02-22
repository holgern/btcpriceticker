import logging
from datetime import datetime

from .coingecko import CoinGecko
from .coinpaprika import CoinPaprika
from .mempool import Mempool

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
        self.interval = interval
        self.available_services = ["mempool", "coingecko", "coinpaprika"]
        if service not in self.available_services:
            raise ValueError("Wrong service!")
        self.services = {}
        self.service = service
        if enable_ohlc:
            self.current_service = "coingecko"
        self.set_service(
            service, fiat, interval, days_ago, enable_ohlc, enable_timeseries
        )
        self.min_refresh_time = min_refresh_time  # seconds
        self.fiat = fiat
        self.enable_ohlc = enable_ohlc
        self.enable_timeseries = enable_timeseries

    def set_next_service(self):
        fiat = self.fiat
        service_name = self.service
        interval = self.interval
        days_ago = self.days_ago
        enable_ohlc = self.enable_ohlc
        enable_timeseries = self.enable_timeseries
        if service_name == "coingecko":
            self.set_service(
                "coinpaprika", fiat, interval, days_ago, enable_ohlc, enable_timeseries
            )
        elif service_name == "coinpaprika":
            self.set_service(
                "mempool", fiat, interval, days_ago, enable_ohlc, enable_timeseries
            )
        elif service_name == "mempool":
            self.set_service(
                "coingecko", fiat, interval, days_ago, enable_ohlc, enable_timeseries
            )

    def set_service(
        self, service_name, fiat, interval, days_ago, enable_ohlc, enable_timeseries
    ):
        service = False
        if service_name in self.services:
            return
        if service_name == "coingecko":
            service = CoinGecko(
                fiat,
                whichcoin="bitcoin",
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
            )
        elif service_name == "coinpaprika":
            service = CoinPaprika(
                fiat,
                whichcoin="btc-bitcoin",
                interval=interval,
                enable_timeseries=enable_timeseries,
            )
        elif service_name == "mempool":
            service = Mempool(
                fiat,
                interval=interval,
                days_ago=days_ago,
                enable_timeseries=enable_timeseries,
            )
        if service:
            self.service = service_name
            self.services[service_name] = service

    def _fetch_prices(self):
        """Fetch prices and OHLC data from Service."""
        if self.service not in self.services:
            self.set_next_service()
        self.services[self.service].update()

    def refresh(self):
        """Refresh the price data if necessary."""
        count = 0
        refresh_sucess = self.update_service()
        while not refresh_sucess and count < 3:
            self.set_next_service()
            refresh_sucess = self.update_service()
            count += 1
        return refresh_sucess

    def update_service(self):
        now = datetime.utcnow()
        current_time = now.timestamp()

        if (
            "timestamp" in self.price
            and current_time - self.price["timestamp"] < self.min_refresh_time
        ):
            return True

        logger.info("Fetching price data...")
        try:
            self._fetch_prices()
            return True
        except Exception as e:
            logger.warning(f"Failed to fetch from  {self.service}: {str(e)}")
        return False

    def get_price_list(self):
        return self.services[self.service].get_price_list()

    def get_timeseries_list(self):
        return self.get_price_list()

    @property
    def timeseries_stack(self):
        return self.get_price_list()

    @property
    def price(self):
        return self.services[self.service].get_price()

    @property
    def ohlc(self):
        return self.services[self.service].ohlc

    def set_days_ago(self, days_ago):
        self.days_ago = days_ago
        for service in self.services:
            self.services[service].days_ago = days_ago

    def get_price_change(self):
        return self.services[self.service].get_price_change()

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
        self.update_service()
        price_now = self.price["fiat"]
        return f"{price_now:,.0f}" if price_now > 1000 else f"{price_now:.5g}"
