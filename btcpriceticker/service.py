import abc
from datetime import datetime

from .price_timeseries import PriceTimeSeries


class Service(metaclass=abc.ABCMeta):
    @abc.abstractclassmethod
    def __init__(self, fiat):
        self.interval(fiat)

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
        self.has_ohlc = False
        self.ohlc = {}
        self.price = {"usd": 0, "sat_usd": 0, "fiat": 0, "sat_fiat": 0, "timestamp": 0}
        self.price_history = PriceTimeSeries()

    def get_name(self):
        return self.name

    def get_price(self):
        return self.price

    def update(self):
        now = datetime.utcnow()
        current_time = now.timestamp()
        self.price["usd"] = self.get_current_price("usd")
        self.price["sat_usd"] = 1e8 / self.price["usd"]
        self.price["fiat"] = self.get_current_price(self.fiat)
        self.price["sat_fiat"] = 1e8 / self.price["fiat"]
        if self.enable_ohlc and self.has_ohlc:
            self.ohlc = self.get_ohlc(self.fiat)
        if self.enable_timeseries:
            self.update_price_history(self.fiat)
        else:
            self.append_current_price(self.price["fiat"])

        self.price["timestamp"] = current_time

    def append_current_price(self, current_price):
        now = datetime.utcnow()
        self.price_history.add_price(now, current_price)

    def get_price_list(self):
        return self.price_history.get_price_list(days=self.days_ago)

    def get_price_change(self):
        change_percentage = self.price_history.get_percentage_change(self.days_ago)
        if not change_percentage:
            return ""
        return f"{change_percentage:+.2f}%"

    @abc.abstractmethod
    def get_current_price(self, currency):
        pass

    @abc.abstractmethod
    def get_history_price(self, currency, existing_timestamp=None):
        pass

    @abc.abstractmethod
    def update_price_history(self, currency):
        pass

    @abc.abstractmethod
    def get_ohlc(self, currency):
        pass
