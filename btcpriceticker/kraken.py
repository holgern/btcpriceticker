import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd

from .service import Service

logger = logging.getLogger(__name__)

CCXT_MODULE = None
try:
    import ccxt

    CCXT_MODULE = "ccxt"
except ImportError:  # pragma: no cover
    ccxt = None  # type: ignore


class Kraken(Service):
    def __init__(
        self,
        fiat: str,
        base_asset: str = "BTC",
        interval: str = "1h",
        days_ago: int = 1,
        enable_timeseries: bool = True,
        enable_ohlc: bool = True,
    ):
        self.base_asset = base_asset.upper()
        self.exchange: Optional[Any] = ccxt.kraken() if CCXT_MODULE else None  # type: ignore[attr-defined]
        self.initialize(
            fiat,
            interval=interval,
            days_ago=days_ago,
            enable_timeseries=enable_timeseries,
            enable_ohlc=enable_ohlc,
        )
        self.name = "kraken"

    def _get_symbol(self, currency: str) -> str:
        quote = currency.upper()
        return f"{self.base_asset}/{quote}"

    def interval_to_seconds(self) -> int:
        unit_multipliers = {"m": 60, "h": 3600, "d": 86400}
        try:
            value, unit = int(self.interval[:-1]), self.interval[-1]
            if unit not in unit_multipliers:
                raise ValueError
            return value * unit_multipliers[unit]
        except (ValueError, IndexError) as exc:  # pragma: no cover
            raise ValueError(f"Invalid interval format {self.interval}") from exc

    def get_current_price(self, currency: str) -> Optional[float]:
        if self.exchange is None:
            return None
        symbol = self._get_symbol(currency)
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            last_price = ticker.get("last") or ticker.get("close")
            return float(last_price) if last_price is not None else None
        except Exception as exc:  # pragma: no cover - network or API errors
            logger.exception(f"Failed to fetch current price for {symbol}: {exc}")
            return None

    def _calculate_since(
        self, existing_timestamp: Optional[list[float]]
    ) -> Optional[int]:
        if not existing_timestamp:
            start = datetime.now(timezone.utc) - timedelta(days=self.days_ago)
            return int(start.timestamp() * 1000)
        step_seconds = self.interval_to_seconds()
        last_timestamp = existing_timestamp[-1] + step_seconds
        return int(last_timestamp * 1000)

    def get_history_price(
        self, currency: str, existing_timestamp: Optional[list[float]] = None
    ) -> list[list[float]]:
        if self.exchange is None:
            return []
        symbol = self._get_symbol(currency)
        since = self._calculate_since(existing_timestamp)
        try:
            return self.exchange.fetch_ohlcv(
                symbol,
                timeframe=self.interval,
                since=since,
            )
        except Exception as exc:  # pragma: no cover - network or API errors
            logger.exception(f"Failed to fetch historical prices for {symbol}: {exc}")
            return []

    def update_price_history(self, currency: str) -> None:
        if self.exchange is None:
            return
        logger.info(
            "Getting historical data for a %s interval from Kraken", self.interval
        )
        existing_timestamp = self.price_history.get_timestamp_list()
        ohlcv_data = self.get_history_price(currency, existing_timestamp)
        for candle in ohlcv_data:
            if len(candle) < 5:
                continue
            timestamp_ms, _, _, _, close_price = candle[:5]
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            self.price_history.add_price(dt, float(close_price))

    def get_ohlc(self, currency: str) -> pd.DataFrame:
        if self.exchange is None:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])
        symbol = self._get_symbol(currency)
        try:
            ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe=self.interval)
        except Exception as exc:  # pragma: no cover - network or API errors
            logger.exception(f"Failed to fetch OHLC data for {symbol}: {exc}")
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        if not ohlcv_data:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        times = [
            datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
            for candle in ohlcv_data
        ]
        values = [candle[1:5] for candle in ohlcv_data]
        df = pd.DataFrame(values, columns=["Open", "High", "Low", "Close"], index=times)
        return df
