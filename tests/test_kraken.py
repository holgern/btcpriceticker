import unittest
from unittest.mock import MagicMock, patch

from btcpriceticker.kraken import Kraken


class TestKraken(unittest.TestCase):
    @patch("btcpriceticker.kraken.ccxt.kraken")
    def test_get_current_price(self, mock_kraken):
        exchange = MagicMock()
        exchange.fetch_ticker.return_value = {"last": 50000}
        mock_kraken.return_value = exchange

        kraken_service = Kraken("EUR")
        price = kraken_service.get_current_price("USD")

        self.assertEqual(price, 50000.0)

    @patch("btcpriceticker.kraken.ccxt.kraken")
    def test_update_price_history(self, mock_kraken):
        exchange = MagicMock()
        exchange.fetch_ohlcv.return_value = [
            [1609459200000, 29000, 29500, 28500, 29200, 10.5],
            [1609462800000, 29200, 29600, 28900, 29450, 8.3],
        ]
        mock_kraken.return_value = exchange

        kraken_service = Kraken("EUR", interval="1h", enable_timeseries=True)
        kraken_service.update_price_history("EUR")

        self.assertGreater(len(kraken_service.price_history.data), 0)
        exchange.fetch_ohlcv.assert_called()

    @patch("btcpriceticker.kraken.ccxt.kraken")
    def test_get_ohlc_with_existing_timestamp(self, mock_kraken):
        exchange = MagicMock()
        exchange.fetch_ohlcv.return_value = [
            [1609459200000, 29000, 29500, 28500, 29200, 10.5],
            [1609462800000, 29200, 29600, 28900, 29450, 8.3],
        ]
        mock_kraken.return_value = exchange

        kraken_service = Kraken("EUR", interval="1h", enable_ohlcv=True)
        existing = [1609455600.0]
        df = kraken_service.get_ohlcv("EUR", existing_timestamp=existing)

        exchange.fetch_ohlcv.assert_called()
        self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
