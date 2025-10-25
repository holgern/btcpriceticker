from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from .service import Service

logger = logging.getLogger(__name__)


class Bit2Me(Service):
    base_url = "https://gateway.bit2me.com"

    def __init__(
        self,
        fiat: str,
        base_asset: str = "BTC",
        interval: str = "1h",
        days_ago: int = 1,
        enable_ohlc: bool = True,
        enable_timeseries: bool = True,
        enable_ohlcv: bool = True,
    ) -> None:
        self.base_asset = base_asset.upper()
        self.session = requests.Session()
        self.api_key = os.getenv("BIT2ME_API_KEY")
        self.api_secret = os.getenv("BIT2ME_API_SECRET")
        self._fiat_rates: dict[str, float] = {}
        self._fiat_rates_timestamp = 0.0
        self.initialize(
            fiat,
            interval=interval,
            days_ago=days_ago,
            enable_ohlc=enable_ohlc,
            enable_timeseries=enable_timeseries,
            enable_ohlcv=enable_ohlcv,
        )
        self.name = "bit2me"

    def _build_headers(
        self, path_url: str, body: dict[str, Any] | None = None
    ) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        if not self.api_key:
            return headers

        headers["x-api-key"] = self.api_key
        nonce = str(int(time.time() * 1000))
        headers["x-nonce"] = nonce

        if not self.api_secret:
            return headers

        message = f"{nonce}:{path_url}"
        if body:
            body_str = json.dumps(body, separators=(",", ":"))
            message += f":{body_str}"

        sha = hashlib.sha256()
        sha.update(message.encode("utf-8"))
        digest = sha.digest()
        signature = hmac.new(
            self.api_secret.encode("utf-8"), digest, hashlib.sha512
        ).digest()
        headers["api-signature"] = base64.b64encode(signature).decode("utf-8")
        return headers

    def _request(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        request = requests.Request(
            method,
            f"{self.base_url}{endpoint}",
            params=params if method.upper() == "GET" else None,
            json=params if method.upper() != "GET" else None,
        )
        prepared = self.session.prepare_request(request)
        body = params if method.upper() != "GET" else None
        headers = self._build_headers(prepared.path_url, body)
        prepared.headers.update(headers)
        try:
            response = self.session.send(prepared, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover - network errors
            logger.exception("Bit2Me request error: %s", exc)
            raise RuntimeError("Failed to reach Bit2Me API") from exc
        if response.status_code >= 400:
            logger.warning(
                "Bit2Me API returned %s for %s", response.status_code, prepared.path_url
            )
            raise RuntimeError(
                f"Bit2Me API error {response.status_code}: {response.text}"
            )
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def _map_chart_temporality(self) -> str | None:
        mapping = {
            "1h": "one-hour",
            "4h": "four-hours",
            "12h": "twelve-hours",
            "1d": "one-day",
            "1w": "one-week",
            "1m": "one-month",
            "3m": "three-months",
            "6m": "six-months",
            "1y": "one-year",
            "max": "all-time",
        }
        return mapping.get(self.interval.lower())

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        table = {
            "1H": 3600,
            "4H": 4 * 3600,
            "12H": 12 * 3600,
            "1D": 24 * 3600,
            "1W": 7 * 24 * 3600,
            "1M": 30 * 24 * 3600,
            "1Y": 365 * 24 * 3600,
        }
        return table.get(timeframe.upper(), 0)

    def _get_usd_price(self) -> float | None:
        try:
            data = self._request("GET", f"/v3/currency/ticker/{self.base_asset}")
        except RuntimeError:
            return None

        if not isinstance(data, dict):
            return None

        usd_bucket = data.get("USD")
        if not isinstance(usd_bucket, dict):
            return None

        asset_entries = usd_bucket.get(self.base_asset)
        if not isinstance(asset_entries, list):
            return None

        for entry in asset_entries:
            if isinstance(entry, dict) and entry.get("price") is not None:
                try:
                    return float(entry["price"])
                except (TypeError, ValueError):
                    continue
        return None

    def _refresh_rates(self) -> None:
        try:
            payload = self._request("GET", "/v1/currency/rate", params={"type": "fiat"})
        except RuntimeError:
            return

        rates: dict[str, float] = {}
        if isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                fiat_section = entry.get("fiat")
                if not isinstance(fiat_section, dict):
                    continue
                for code, value in fiat_section.items():
                    try:
                        rates[code.upper()] = float(value)
                    except (TypeError, ValueError):
                        continue

        if rates:
            rates["USD"] = 1.0
            self._fiat_rates = rates
            self._fiat_rates_timestamp = time.time()

    def _extract_rate(self, payload: Any, currency: str) -> float | None:
        if not isinstance(payload, list):
            return None
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            fiat_section = entry.get("fiat")
            if not isinstance(fiat_section, dict):
                continue
            raw_rate = fiat_section.get(currency.upper())
            if raw_rate is None:
                continue
            try:
                return float(raw_rate)
            except (TypeError, ValueError):
                continue
        return None

    def _get_fiat_rate(self, currency: str) -> float | None:
        code = currency.upper()
        if code == "USD":
            return 1.0

        now = time.time()
        if not self._fiat_rates or (now - self._fiat_rates_timestamp) > 300:
            self._refresh_rates()

        rate = self._fiat_rates.get(code)
        if rate is not None:
            return rate

        # Attempt one more refresh in case rates were missing
        self._refresh_rates()
        return self._fiat_rates.get(code)

    def _fetch_ohlc_point(
        self, timeframe: str, currency: str, target_dt: datetime
    ) -> tuple[datetime, dict[str, float]] | None:
        iso_time = target_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        rate_time = str(int(target_dt.timestamp() * 1000))
        try:
            usd_values = self._request(
                "GET",
                f"/v1/currency/ohlca/{self.base_asset}",
                params={"timeframe": timeframe, "time": iso_time},
            )
        except RuntimeError:
            return None

        if not isinstance(usd_values, dict):
            return None

        try:
            rate_payload = self._request(
                "GET",
                "/v1/currency/rate",
                params={"type": "fiat", "time": rate_time},
            )
        except RuntimeError:
            return None

        rate_value = self._extract_rate(rate_payload, currency)
        if rate_value is None:
            logger.warning("Bit2Me ohlc rate missing for %s", currency)
            return None

        try:
            open_price = float(usd_values["open"]) * rate_value
            high_price = float(usd_values["high"]) * rate_value
            low_price = float(usd_values["low"]) * rate_value
            close_price = float(usd_values["close"]) * rate_value
        except (KeyError, TypeError, ValueError):
            return None

        return (
            target_dt,
            {
                "Open": open_price,
                "High": high_price,
                "Low": low_price,
                "Close": close_price,
            },
        )

    def get_current_price(self, currency: str) -> float | None:
        usd_price = self._get_usd_price()
        if usd_price is None:
            return None

        rate = self._get_fiat_rate(currency)
        if rate is None:
            logger.warning("Bit2Me rate for %s not found", currency)
            return usd_price if currency.upper() == "USD" else None

        return usd_price * rate

    def _chart(self, currency: str) -> list[list[Any]]:
        params = {"ticker": f"{self.base_asset}/{currency.upper()}"}
        temporality = self._map_chart_temporality()
        if temporality:
            params["temporality"] = temporality
        try:
            data = self._request("GET", "/v3/currency/chart", params=params)
        except RuntimeError:
            return []
        if isinstance(data, list):
            return data
        return []

    def get_history_price(
        self, currency: str, existing_timestamp: list[float] | None = None
    ) -> list[list[float]]:
        chart = self._chart(currency)
        if not chart:
            return []
        last_ts = existing_timestamp[-1] if existing_timestamp else None
        history: list[list[float]] = []
        for entry in chart:
            if not entry:
                continue
            try:
                timestamp_ms = float(entry[0])
                inverse_price = float(entry[1])
                multiplier = float(entry[2])
            except (TypeError, ValueError, IndexError):
                continue

            if inverse_price == 0:
                continue

            timestamp_sec = timestamp_ms / 1000
            if last_ts and timestamp_sec <= last_ts:
                continue

            price_value = (1.0 / inverse_price) * multiplier
            history.append([timestamp_ms, price_value])
        return history

    def update_price_history(self, currency: str) -> None:
        data = self.get_history_price(
            currency, existing_timestamp=self.price_history.get_timestamp_list()
        )
        for timestamp_ms, price in data:
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            self.price_history.add_price(dt, price)

    def get_ohlcv(
        self, currency: str, existing_timestamp: list[float] | None = None
    ) -> pd.DataFrame:
        ohlc_df = self.get_ohlc(currency, existing_timestamp)
        if ohlc_df.empty:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        ohlcv_df = ohlc_df.copy()
        ohlcv_df["Volume"] = 0.0
        return ohlcv_df

    def get_ohlc(
        self, currency: str, existing_timestamp: list[float] | None = None
    ) -> pd.DataFrame:
        timeframe = self.interval.upper()
        interval_seconds = self._timeframe_to_seconds(timeframe)
        if interval_seconds <= 0:
            interval_seconds = 3600

        now_dt = datetime.now(timezone.utc)
        now_ts = int(now_dt.timestamp())
        now_ts -= now_ts % interval_seconds
        now_dt = datetime.fromtimestamp(now_ts, tz=timezone.utc)

        rows: list[tuple[datetime, dict[str, float]]] = []
        seen = {int(ts) for ts in (existing_timestamp or [])}

        if existing_timestamp:
            last_ts = int(existing_timestamp[-1])
            start_ts = last_ts + interval_seconds
        else:
            window_seconds = max(self.days_ago * 86400, interval_seconds)
            periods = max(1, math.ceil(window_seconds / interval_seconds))
            start_ts = now_ts - (periods - 1) * interval_seconds

        current_ts = start_ts
        while current_ts <= now_ts:
            if current_ts in seen:
                current_ts += interval_seconds
                continue
            target_dt = datetime.fromtimestamp(current_ts, tz=timezone.utc)
            point = self._fetch_ohlc_point(timeframe, currency, target_dt)
            if point is not None:
                ts, values = point
                int_ts = int(ts.timestamp())
                if int_ts not in seen:
                    rows.append((ts, values))
                    seen.add(int_ts)
            current_ts += interval_seconds

        if not rows:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close"])

        rows.sort(key=lambda item: item[0])
        index = [ts for ts, _ in rows]
        data = [values for _, values in rows]
        df = pd.DataFrame(data, index=index)
        df.index.name = "timestamp"
        return df
