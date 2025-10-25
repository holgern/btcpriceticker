import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd
from pytest import approx

from btcpriceticker.bit2me import Bit2Me


class TestBit2Me(unittest.TestCase):
    def test_get_current_price_converts_with_rate(self):
        with (
            patch.object(Bit2Me, "_get_usd_price", return_value=50000.0),
            patch.object(Bit2Me, "_get_fiat_rate", return_value=0.9),
        ):
            service = Bit2Me("EUR")
            price = service.get_current_price("EUR")

        self.assertEqual(price, 45000.0)

    def test_get_history_price_from_chart(self):
        chart_data = [
            [1712497400000, "0.00005", "0.9"],
            [1712498400000, "0.00004", "0.9"],
        ]
        with patch.object(Bit2Me, "_chart", return_value=chart_data):
            service = Bit2Me("EUR")
            history = service.get_history_price("EUR")

        prices = [entry[1] for entry in history]
        assert prices[0] == approx(18000.0)
        assert prices[1] == approx(22500.0)

    def test_update_price_history_stores_converted_values(self):
        chart_data = [
            [1712497400000, "0.00005", "0.8"],
            [1712498400000, "0.00005", "0.82"],
        ]
        with patch.object(Bit2Me, "_chart", return_value=chart_data):
            service = Bit2Me("EUR")
            service.update_price_history("EUR")

        prices = service.price_history.data["price"].tolist()
        assert prices[0] == approx(16000.0)
        assert prices[1] == approx(16400.0)

    def test_fetch_ohlc_point_converts_prices(self):
        service = Bit2Me("EUR")
        target_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        with patch.object(
            Bit2Me,
            "_request",
            side_effect=[
                {"open": "100.0", "high": "110.0", "low": "90.0", "close": "105.0"},
                [{"fiat": {"EUR": "0.9"}}],
            ],
        ):
            result = service._fetch_ohlc_point("1H", "EUR", target_dt)

        self.assertIsNotNone(result)
        assert result is not None  # for type checkers
        ts, data = result
        self.assertEqual(ts, target_dt)
        assert data["Open"] == approx(90.0)
        assert data["High"] == approx(99.0)
        assert data["Low"] == approx(81.0)
        assert data["Close"] == approx(94.5)

    def test_get_ohlc_returns_multiple_rows(self):
        service = Bit2Me("EUR", interval="12h")
        service.days_ago = 1

        with patch.object(Bit2Me, "_fetch_ohlc_point", autospec=True) as mock_fetch:

            def fake_fetch(self, timeframe, currency, target_dt):
                base = target_dt.timestamp()
                return (
                    target_dt,
                    {
                        "Open": base,
                        "High": base + 1,
                        "Low": base - 1,
                        "Close": base + 0.5,
                    },
                )

            mock_fetch.side_effect = fake_fetch
            df = service.get_ohlc("EUR")

        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertListEqual(list(df.columns), ["Open", "High", "Low", "Close"])
        self.assertEqual(len(df), 2)

    def test_get_ohlcv_adds_volume(self):
        service = Bit2Me("EUR")

        with patch.object(Bit2Me, "_fetch_ohlc_point", autospec=True) as mock_fetch:

            def fake_fetch(self, timeframe, currency, target_dt):
                return (
                    target_dt,
                    {
                        "Open": 100.0,
                        "High": 110.0,
                        "Low": 90.0,
                        "Close": 105.0,
                    },
                )

            mock_fetch.side_effect = fake_fetch
            df = service.get_ohlcv("EUR")

        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertListEqual(
            list(df.columns), ["Open", "High", "Low", "Close", "Volume"]
        )
        assert df.iloc[0]["Volume"] == 0.0


if __name__ == "__main__":
    unittest.main()
