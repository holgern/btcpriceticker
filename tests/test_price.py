import unittest
from unittest.mock import patch

from btcpriceticker.coingecko import CoinGecko
from btcpriceticker.coinpaprika import CoinPaprika
from btcpriceticker.mempool import Mempool
from btcpriceticker.price import Price


class TestPrice(unittest.TestCase):
    @patch.object(CoinGecko, "get_current_price")
    @patch.object(CoinGecko, "get_ohlc")
    @patch.object(CoinGecko, "get_history_price")
    def test_refresh_with_coingecko(
        self, mock_get_history_price, mock_get_ohlc, mock_get_current_price
    ):
        # Mock responses
        mock_get_current_price.side_effect = lambda currency: {
            "usd": 50000,
            "eur": 42000,
        }[currency]
        mock_get_ohlc.return_value = {
            "Open": 49000,
            "High": 51000,
            "Low": 48000,
            "Close": 50000,
        }
        mock_get_history_price.return_value = [40000, 50000]

        price_instance = Price(fiat="eur", days_ago=1)
        self.assertTrue(price_instance.refresh())

        self.assertEqual(price_instance.price["usd"], 50000)
        self.assertEqual(price_instance.price["fiat"], 42000)
        self.assertEqual(price_instance.price["sat_usd"], 2000.0)
        self.assertEqual(price_instance.price["sat_fiat"], 2380.9523809523807)
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(CoinPaprika, "get_current_price")
    def test_refresh_with_paprika(self, mock_get_current_price):
        # Mock responses
        mock_get_current_price.side_effect = lambda currency: {
            "USD": 50000,
            "EUR": 42000,
        }[currency]

        price_instance = Price(fiat="eur", days_ago=1, service="coinpaprika")

        self.assertTrue(price_instance.refresh())

        self.assertEqual(price_instance.price["usd"], 50000)
        self.assertEqual(price_instance.price["fiat"], 42000)
        self.assertEqual(price_instance.price["sat_usd"], 2000.0)
        self.assertEqual(price_instance.price["sat_fiat"], 2380.9523809523807)
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(Mempool, "get_current_price")
    def test_refresh_with_mempool(self, mock_get_current_price):
        # Mock responses
        mock_get_current_price.side_effect = lambda currency: {
            "USD": 50000,
            "EUR": 42000,
        }[currency]

        price_instance = Price(fiat="eur", days_ago=1, service="mempool")

        self.assertTrue(price_instance.refresh())

        self.assertEqual(price_instance.price["usd"], 50000)
        self.assertEqual(price_instance.price["fiat"], 42000)
        self.assertEqual(price_instance.price["sat_usd"], 2000.0)
        self.assertEqual(price_instance.price["sat_fiat"], 2380.9523809523807)
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(CoinGecko, "get_history_price")
    def test_get_price_now(self, mock_get_history_price):
        mock_get_history_price.return_value = [40000, 50000]
        price_instance = Price(fiat="eur", days_ago=1)
        price_instance.refresh()

        self.assertEqual(price_instance.get_price_now(), "50,000")

    def test_set_days_ago(self):
        price_instance = Price(fiat="eur", days_ago=1)
        price_instance.set_days_ago(7)
        self.assertEqual(price_instance.days_ago, 7)


if __name__ == "__main__":
    unittest.main()
