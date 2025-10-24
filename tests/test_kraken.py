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


if __name__ == "__main__":
    unittest.main()
