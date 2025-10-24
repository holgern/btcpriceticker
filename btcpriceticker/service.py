import abc
from datetime import datetime, timezone
from typing import Any, Optional

from .price_timeseries import PriceTimeSeries


class Service(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, fiat):
        self.initialize(fiat)

    def initialize(
        self,
        fiat,
        interval="1h",
        days_ago=1,
        enable_ohlc=False,
        enable_timeseries=False,
    ):
        self.interval = interval
        self.days_ago = days_ago
        self.name = ""
        self.fiat = fiat
        self.enable_ohlc = enable_ohlc
        self.enable_timeseries = enable_timeseries
        self.ohlc = {}
        self.price = {
            "usd": 0.0,
            "sat_usd": 0.0,
            "fiat": 0.0,
            "sat_fiat": 0.0,
            "timestamp": 0.0,
        }
        self.price_history = PriceTimeSeries()

    def get_name(self):
        return self.name

    def get_price(self):
        return self.price

    def _safe_get_current_price(self, currency: str) -> Optional[float]:
        variations = (currency, currency.upper(), currency.lower())
        for variant in variations:
            try:
                price = self.get_current_price(variant)
            except Exception:
                continue
            if price is not None:
                return price
        return None

    def update(self):
        now = datetime.now(timezone.utc)
        current_time = now.timestamp()

        # Get USD price, defaulting to 0.0 if None is returned
        usd_price = self._safe_get_current_price("USD")
        self.price["usd"] = usd_price if usd_price is not None else 0.0
        self.price["sat_usd"] = 1e8 / self.price["usd"] if self.price["usd"] else 0.0

        # Get fiat price, defaulting to 0.0 if None is returned
        fiat_price = self._safe_get_current_price(self.fiat)
        self.price["fiat"] = fiat_price if fiat_price is not None else 0.0
        self.price["sat_fiat"] = 1e8 / self.price["fiat"] if self.price["fiat"] else 0.0

        if self.enable_timeseries:
            self.update_price_history(self.fiat)
        else:
            self.append_current_price(self.price["fiat"])
        if self.enable_ohlc:
            self.ohlc = self.get_ohlc(self.fiat)

        self.price["timestamp"] = current_time

    def append_current_price(self, current_price):
        now = datetime.now(timezone.utc)
        self.price_history.add_price(now, current_price)

    def get_price_list(self):
        return self.price_history.get_price_list(days=self.days_ago)

    def get_price_change(self):
        change_percentage = self.price_history.get_percentage_change(self.days_ago)
        if not change_percentage:
            return ""
        return f"{change_percentage:+.2f}%"

    @abc.abstractmethod
    def get_current_price(self, currency) -> Optional[float]:
        pass

    @abc.abstractmethod
    def get_history_price(self, currency, existing_timestamp=None) -> Any:
        pass

    @abc.abstractmethod
    def update_price_history(self, currency) -> None:
        pass

    @abc.abstractmethod
    def get_ohlc(self, currency) -> dict:
        pass
