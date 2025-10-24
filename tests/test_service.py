import unittest
from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import patch

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

    def get_ohlc(self, currency) -> dict:
        # Mock implementation returns fixed OHLC data
        return {
            "Open": 49000,
            "High": 51000,
            "Low": 48000,
            "Close": 50000,
        }


class TestService(unittest.TestCase):
    def setUp(self):
        self.service = MockService("eur")

    def test_initialize(self):
        """Test initialization of the Service class."""
        self.assertEqual(self.service.fiat, "eur")
        self.assertEqual(self.service.days_ago, 1)
        self.assertEqual(self.service.name, "mock_service")
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

    def test_update_with_ohlc_enabled(self):
        """Test update with OHLC enabled."""
        self.service.enable_ohlc = True

        # Need to patch get_ohlc to verify it's called
        with patch.object(MockService, "get_ohlc") as mock_ohlc:
            mock_ohlc.return_value = {
                "Open": 49000,
                "High": 51000,
                "Low": 48000,
                "Close": 50000,
            }
            self.service.update()
            mock_ohlc.assert_called_once_with("eur")
            self.assertEqual(self.service.ohlc["Open"], 49000)


if __name__ == "__main__":
    unittest.main()
