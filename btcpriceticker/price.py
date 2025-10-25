import logging
from datetime import datetime, timezone
from typing import Optional

from .binance import Binance
from .bit2me import Bit2Me
from .bitvavo import Bitvavo
from .coinbase import Coinbase
from .coingecko import CoinGecko
from .coinpaprika import CoinPaprika
from .kraken import Kraken
from .mempool import Mempool
from .price_timeseries import PriceTimeSeries
from .service import Service

logger = logging.getLogger(__name__)


class Price:
    def __init__(
        self,
        fiat: str = "eur",
        days_ago: int = 1,
        min_refresh_time: int = 120,
        interval: str = "1h",
        ohlcv_interval: str = "1h",
        service: str = "mempool",
        enable_ohlcv: bool = False,
        enable_ohlc: bool = False,
        enable_timeseries: bool = True,
    ) -> None:
        self.days_ago = days_ago
        self.interval = interval
        self.available_services = [
            "mempool",
            "coingecko",
            "coinpaprika",
            "kraken",
            "binance",
            "coinbase",
            "bitvavo",
            "bit2me",
        ]
        if service not in self.available_services:
            raise ValueError("Wrong service!")
        self.services: dict[str, Service] = {}
        self.service = service
        self.enable_ohlcv = enable_ohlcv or enable_ohlc
        self.set_service(
            service,
            fiat,
            interval,
            days_ago,
            enable_ohlc,
            enable_timeseries,
            enable_ohlcv,
        )
        self.min_refresh_time = min_refresh_time  # seconds
        self.fiat = fiat
        self.enable_ohlc = enable_ohlc
        self.enable_ohlcv = enable_ohlcv
        self.enable_timeseries = enable_timeseries

    def set_next_service(self, next_service: Optional[str] = None) -> None:
        fiat = self.fiat
        service_name = self.service
        interval = self.interval
        days_ago = self.days_ago
        enable_ohlc = self.enable_ohlc
        enable_ohlcv = self.enable_ohlcv
        enable_timeseries = self.enable_timeseries
        if next_service is None:
            rotation = [
                "mempool",
                "coingecko",
                "coinpaprika",
                "kraken",
                "binance",
                "coinbase",
                "bitvavo",
                "bit2me",
            ]
            try:
                current_index = rotation.index(service_name)
            except ValueError:
                current_index = -1
            next_service = rotation[(current_index + 1) % len(rotation)]

        self.set_service(
            next_service,
            fiat,
            interval,
            days_ago,
            enable_ohlc,
            enable_timeseries,
            enable_ohlcv,
        )

    def set_service(
        self,
        service_name: str,
        fiat: str,
        interval: str,
        days_ago: int,
        enable_ohlc: bool,
        enable_timeseries: bool,
        enable_ohlcv: bool,
    ) -> None:
        if service_name in self.services:
            self.service = service_name
            return

        service_instance: Optional[Service] = None
        if service_name == "coingecko":
            service_instance = CoinGecko(
                fiat,
                whichcoin="bitcoin",
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "coinpaprika":
            service_instance = CoinPaprika(
                fiat,
                whichcoin="btc-bitcoin",
                interval=interval,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "mempool":
            service_instance = Mempool(
                fiat,
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "kraken":
            service_instance = Kraken(
                fiat,
                base_asset="BTC",
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "binance":
            service_instance = Binance(
                fiat,
                base_asset="BTC",
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "coinbase":
            service_instance = Coinbase(
                fiat,
                base_asset="BTC",
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "bitvavo":
            service_instance = Bitvavo(
                fiat,
                base_asset="BTC",
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )
        elif service_name == "bit2me":
            service_instance = Bit2Me(
                fiat,
                base_asset="BTC",
                interval=interval,
                days_ago=days_ago,
                enable_ohlc=enable_ohlc,
                enable_timeseries=enable_timeseries,
                enable_ohlcv=enable_ohlcv,
            )

        if service_instance is None:
            raise ValueError(f"Unsupported service '{service_name}'")

        self.service = service_name
        self.services[service_name] = service_instance

    def _fetch_prices(self):
        """Fetch prices and OHLCV data from Service."""
        if self.service not in self.services:
            self.set_next_service()
        self.services[self.service].update()

    def refresh(self):
        """Refresh the price data if necessary."""
        count = 0
        refresh_sucess = self.update_service()
        old_service_name = self.service
        while not refresh_sucess and count < 3:
            self.set_next_service()
            refresh_sucess = self.update_service()
            count += 1

        self.set_next_service(next_service=old_service_name)
        return refresh_sucess

    def update_service(self):
        now = datetime.now(timezone.utc)
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

    @property
    def ohlcv(self):
        return self.services[self.service].ohlcv

    def set_days_ago(self, days_ago: int) -> None:
        self.days_ago = days_ago
        for service in self.services:
            self.services[service].days_ago = days_ago

    def get_price_change(self) -> str:
        return self.services[self.service].get_price_change()

    def get_fiat_price(self) -> float:
        return self.price["fiat"]

    def get_usd_price(self) -> float:
        return self.price["usd"]

    def get_sats_per_fiat(self) -> float:
        return 1e8 / self.price["fiat"]

    def get_sats_per_usd(self) -> float:
        return 1e8 / self.price["usd"]

    def get_timestamp(self) -> float:
        return self.price["timestamp"]

    def get_price_now(self) -> str:
        self.update_service()
        price_now = self.price["fiat"]
        return f"{price_now:,.0f}" if price_now > 1000 else f"{price_now:.5g}"

    @property
    def timeseries(self) -> PriceTimeSeries:
        return self.services[self.service].price_history
