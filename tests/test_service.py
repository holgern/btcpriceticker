import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from unittest.mock import patch

import pandas as pd

from btcpriceticker.price_timeseries import PriceTimeSeries
from btcpriceticker.service import Service


class MockService(Service):
    """Mock implementation of the abstract Service class for testing."""

    def __init__(self, fiat="usd"):
        self.initialize(fiat)
        self.name = "mock_service"

    def get_current_price(self, currency) -> Optional[float]:
        # Mock implementation returns fixed values based on currency
        if currency.lower() == "usd":
            return 50000
        return 42000

    def get_history_price(self, currency, existing_timestamp=None) -> Any:
        # Mock implementation returns fixed history
        # Return a simple list of price values
        return [40000, 50000]

    def update_price_history(self, currency) -> None:
        # Mock implementation adds a fixed price
        now = datetime.now(timezone.utc)
        self.price_history.add_price(now, 50000)

    def get_ohlc(self, currency, existing_timestamp=None) -> pd.DataFrame:
        base_time = datetime.now(timezone.utc)
        if existing_timestamp:
            base_time = datetime.fromtimestamp(existing_timestamp[-1], tz=timezone.utc)
        index = pd.date_range(base_time + timedelta(hours=1), periods=1, freq="h")
        return pd.DataFrame(
            [[49000, 51000, 48000, 50000]],
            columns=["Open", "High", "Low", "Close"],
            index=index,
        )

    def get_ohlcv(self, currency, existing_timestamp=None) -> pd.DataFrame:
        base_time = datetime.now(timezone.utc)
        if existing_timestamp:
            base_time = datetime.fromtimestamp(existing_timestamp[-1], tz=timezone.utc)
        index = pd.date_range(base_time + timedelta(hours=1), periods=1, freq="h")
        return pd.DataFrame(
            [[49000, 51000, 48000, 50000, 12345]],
            columns=["Open", "High", "Low", "Close", "Volume"],
            index=index,
        )


class TestService(unittest.TestCase):
    def setUp(self):
        self.service = MockService("eur")

    def test_initialize(self):
        """Test initialization of the Service class."""
        self.assertEqual(self.service.fiat, "eur")
        self.assertEqual(self.service.days_ago, 1)
        self.assertEqual(self.service.name, "mock_service")
        self.assertFalse(self.service.enable_ohlcv)
        self.assertFalse(self.service.enable_ohlc)
        self.assertFalse(self.service.enable_timeseries)
        self.assertEqual(self.service.price["usd"], 0)
        self.assertEqual(self.service.price["fiat"], 0)
        self.assertIsInstance(self.service.price_history, PriceTimeSeries)

    def test_get_name(self):
        """Test get_name method."""
        self.assertEqual(self.service.get_name(), "mock_service")

    def test_get_price(self):
        """Test get_price method."""
        self.assertEqual(self.service.get_price(), self.service.price)

    def test_update(self):
        """Test update method."""
        self.service.update()

        # Check USD and fiat prices are updated
        self.assertEqual(self.service.price["usd"], 50000)
        self.assertEqual(self.service.price["fiat"], 42000)

        # Check sat conversions
        self.assertEqual(self.service.price["sat_usd"], 1e8 / 50000)
        self.assertEqual(self.service.price["sat_fiat"], 1e8 / 42000)

        # Check timestamp is updated
        self.assertGreater(self.service.price["timestamp"], 0)

    def test_update_with_zero_price(self):
        """Test update method with zero price handling."""
        with patch.object(MockService, "get_current_price", return_value=0):
            self.service.update()

            # Check sat values are zero when price is zero
            self.assertEqual(self.service.price["sat_usd"], 0)
            self.assertEqual(self.service.price["sat_fiat"], 0)

    def test_append_current_price(self):
        """Test append_current_price method."""
        initial_count = len(self.service.price_history.get_price_list())
        self.service.append_current_price(50000)
        new_count = len(self.service.price_history.get_price_list())

        # Verify a price was added to the history
        self.assertEqual(new_count, initial_count + 1)

    def test_get_price_list(self):
        """Test get_price_list method."""
        # Mock the price_history.get_price_list method to avoid timezone issues
        with patch.object(PriceTimeSeries, "get_price_list", return_value=[50000]):
            price_list = self.service.get_price_list()

            # Verify we get a list of prices
            self.assertIsInstance(price_list, list)
            self.assertEqual(price_list, [50000])

    def test_get_price_change(self):
        """Test get_price_change method."""
        # Mock the get_percentage_change method to return a known value
        with patch.object(PriceTimeSeries, "get_percentage_change", return_value=5.25):
            change = self.service.get_price_change()
            self.assertEqual(change, "+5.25%")

        # Test with no change
        with patch.object(PriceTimeSeries, "get_percentage_change", return_value=None):
            change = self.service.get_price_change()
            self.assertEqual(change, "")

    def test_update_with_timeseries_enabled(self):
        """Test update with timeseries enabled."""
        self.service.enable_timeseries = True

        # Need to patch update_price_history to verify it's called
        with patch.object(MockService, "update_price_history") as mock_update:
            self.service.update()
            mock_update.assert_called_once_with("eur")

    def test_update_with_ohlcv_enabled(self):
        """Test update with OHLCV enabled."""
        self.service.enable_ohlcv = True

        # Need to patch get_ohlcv to verify it's called
        with patch.object(MockService, "get_ohlcv") as mock_ohlcv:
            mock_ohlcv.return_value = pd.DataFrame(
                [[49000, 51000, 48000, 50000, 12345]],
                columns=["Open", "High", "Low", "Close", "Volume"],
                index=pd.date_range(datetime.now(timezone.utc), periods=1, freq="h"),
            )
            self.service.update()
            mock_ohlcv.assert_called_once()
            args, kwargs = mock_ohlcv.call_args
            self.assertEqual(args[0], "eur")
            self.assertIn("existing_timestamp", kwargs)
            self.assertIsInstance(self.service.ohlcv, pd.DataFrame)
            self.assertFalse(self.service.ohlcv.empty)

    def test_update_with_ohlc_enabled(self):
        """Test update with OHLC enabled."""
        self.service.enable_ohlc = True

        with patch.object(MockService, "get_ohlc") as mock_ohlc:
            mock_ohlc.return_value = pd.DataFrame(
                [[49000, 51000, 48000, 50000]],
                columns=["Open", "High", "Low", "Close"],
                index=pd.date_range(datetime.now(timezone.utc), periods=1, freq="h"),
            )
            self.service.update()
            mock_ohlc.assert_called_once()
            args, kwargs = mock_ohlc.call_args
            self.assertEqual(args[0], "eur")
            self.assertIn("existing_timestamp", kwargs)
            self.assertIsInstance(self.service.ohlc, pd.DataFrame)
            self.assertFalse(self.service.ohlc.empty)

    def test_update_ohlcv_accumulates(self):
        self.service.enable_ohlcv = True
        with patch.object(MockService, "get_ohlcv") as mock_ohlcv:
            base_time = datetime.now(timezone.utc)
            first_df = pd.DataFrame(
                [[49000, 51000, 48000, 50000, 12345]],
                columns=["Open", "High", "Low", "Close", "Volume"],
                index=pd.date_range(base_time, periods=1, freq="h"),
            )
            second_df = pd.DataFrame(
                [[50010, 51500, 48500, 50500, 23456]],
                columns=["Open", "High", "Low", "Close", "Volume"],
                index=pd.date_range(
                    base_time + timedelta(hours=1), periods=1, freq="h"
                ),
            )
            mock_ohlcv.side_effect = [first_df, second_df]

            self.service.update()
            self.service.update()

            self.assertEqual(len(self.service.ohlcv), 2)
            self.assertTrue((self.service.ohlcv.iloc[0] == first_df.iloc[0]).all())
            self.assertTrue((self.service.ohlcv.iloc[1] == second_df.iloc[0]).all())


if __name__ == "__main__":
    unittest.main()
