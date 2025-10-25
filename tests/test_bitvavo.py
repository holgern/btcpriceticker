import unittest
from unittest.mock import MagicMock, patch

from btcpriceticker.bitvavo import Bitvavo


class TestBitvavo(unittest.TestCase):
    @patch("btcpriceticker.bitvavo.ccxt.bitvavo")
    def test_get_current_price(self, mock_bitvavo):
        exchange = MagicMock()
        exchange.fetch_ticker.return_value = {"last": 50000}
        mock_bitvavo.return_value = exchange

        service = Bitvavo("EUR")
        price = service.get_current_price("USD")

        self.assertEqual(price, 50000.0)

    @patch("btcpriceticker.bitvavo.ccxt.bitvavo")
    def test_update_price_history(self, mock_bitvavo):
        exchange = MagicMock()
        exchange.fetch_ohlcv.return_value = [
            [1609459200000, 29000, 29500, 28500, 29200, 10.5],
            [1609462800000, 29200, 29600, 28900, 29450, 8.3],
        ]
        mock_bitvavo.return_value = exchange

        service = Bitvavo("EUR", interval="1h", enable_timeseries=True)
        service.update_price_history("EUR")

        self.assertGreater(len(service.price_history.data), 0)
        exchange.fetch_ohlcv.assert_called()

    @patch("btcpriceticker.bitvavo.ccxt.bitvavo")
    def test_get_ohlc_with_existing_timestamp(self, mock_bitvavo):
        exchange = MagicMock()
        exchange.fetch_ohlcv.return_value = [
            [1609459200000, 29000, 29500, 28500, 29200, 10.5],
            [1609462800000, 29200, 29600, 28900, 29450, 8.3],
        ]
        mock_bitvavo.return_value = exchange

        service = Bitvavo("EUR", interval="1h", enable_ohlcv=True)
        existing = [1609455600.0]
        df = service.get_ohlcv("EUR", existing_timestamp=existing)

        exchange.fetch_ohlcv.assert_called()
        self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
