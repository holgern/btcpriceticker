import unittest
from datetime import datetime
from unittest.mock import patch

from btcpriceticker.coingecko import CoinGecko
from btcpriceticker.coinpaprika import CoinPaprika
from btcpriceticker.mempool import Mempool
from btcpriceticker.price import Price


class TestPrice(unittest.TestCase):
    @patch.object(CoinGecko, "get_current_price")
    @patch.object(CoinGecko, "get_ohlc")
    @patch.object(CoinGecko, "get_history_price")
    @patch("btcpriceticker.price_timeseries.PriceTimeSeries.get_price_list")
    def test_refresh_with_coingecko(
        self,
        mock_get_price_list,
        mock_get_history_price,
        mock_get_ohlc,
        mock_get_current_price,
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
        mock_get_history_price.return_value = {"prices": [[1000, 40000], [2000, 50000]]}
        # Mock price_list to return a non-empty list
        mock_get_price_list.return_value = [40000, 50000]

        price_instance = Price(fiat="eur", days_ago=1, service="coingecko")
        self.assertTrue(price_instance.refresh())

        self.assertTrue(price_instance.price["usd"])
        self.assertTrue(price_instance.price["fiat"])
        self.assertTrue(price_instance.price["sat_usd"])
        self.assertTrue(price_instance.price["sat_fiat"])
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(CoinPaprika, "get_current_price")
    @patch.object(CoinPaprika, "update_price_history")
    @patch.object(CoinPaprika, "get_history_price")
    @patch.object(CoinPaprika, "get_ohlc")
    @patch("btcpriceticker.price_timeseries.PriceTimeSeries.get_price_list")
    def test_refresh_with_paprika(
        self,
        mock_get_price_list,
        mock_get_ohlc,
        mock_get_history_price,
        mock_update_price_history,
        mock_get_current_price,
    ):
        # Mock responses
        mock_get_current_price.side_effect = lambda currency: {
            "USD": 50000,
            "EUR": 42000,
        }[currency]

        # Mock price history methods
        mock_update_price_history.return_value = None
        mock_get_history_price.return_value = [
            {"timestamp": "2023-01-01T12:00:00Z", "price": 42000}
        ]
        mock_get_ohlc.return_value = {
            "Open": 41000,
            "High": 43000,
            "Low": 40000,
            "Close": 42000,
        }
        # Mock price_list to return a non-empty list
        mock_get_price_list.return_value = [40000, 50000]

        price_instance = Price(
            fiat="eur", days_ago=1, service="coinpaprika", enable_timeseries=True
        )

        self.assertTrue(price_instance.refresh())

        self.assertTrue(price_instance.price["usd"])
        self.assertTrue(price_instance.price["fiat"])
        self.assertTrue(price_instance.price["sat_usd"])
        self.assertTrue(price_instance.price["sat_fiat"])
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(Mempool, "get_current_price")
    @patch.object(Mempool, "update_price_history")
    @patch.object(Mempool, "get_history_price")
    @patch.object(Mempool, "get_ohlc")
    @patch("btcpriceticker.price_timeseries.PriceTimeSeries.get_price_list")
    def test_refresh_with_mempool(
        self,
        mock_get_price_list,
        mock_get_ohlc,
        mock_get_history_price,
        mock_update_price_history,
        mock_get_current_price,
    ):
        # Mock responses
        mock_get_current_price.side_effect = lambda currency: {
            "USD": 50000,
            "EUR": 42000,
        }[currency]

        # Mock price history methods
        mock_update_price_history.return_value = None
        mock_get_history_price.return_value = [(datetime.now(), 42000)]
        mock_get_ohlc.return_value = {
            "Open": 41000,
            "High": 43000,
            "Low": 40000,
            "Close": 42000,
        }
        # Mock price_list to return a non-empty list
        mock_get_price_list.return_value = [40000, 50000]

        # Create Price instance with both timeseries and OHLC enabled
        price_instance = Price(
            fiat="eur",
            days_ago=1,
            service="mempool",
            enable_timeseries=True,
            enable_ohlc=True,
        )

        self.assertTrue(price_instance.refresh())

        # Verify price data was properly set
        self.assertTrue(price_instance.price["usd"])
        self.assertTrue(price_instance.price["fiat"])
        self.assertTrue(price_instance.price["sat_usd"])
        self.assertTrue(price_instance.price["sat_fiat"])
        self.assertTrue(price_instance.timeseries_stack)

    @patch.object(CoinGecko, "get_current_price")
    @patch.object(CoinGecko, "update_price_history")
    @patch.object(CoinGecko, "get_history_price")
    def test_get_price_now(
        self, mock_get_history_price, mock_update_price_history, mock_get_current_price
    ):
        # Mock the necessary methods
        mock_get_history_price.return_value = {"prices": [[1000, 40000], [2000, 50000]]}
        mock_update_price_history.return_value = None
        mock_get_current_price.side_effect = lambda currency: {
            "usd": 50000,
            "eur": 42000,
        }[currency]

        price_instance = Price(fiat="eur", days_ago=1, service="coingecko")
        price_instance.refresh()

        self.assertTrue(price_instance.get_price_now())

    def test_set_days_ago(self):
        price_instance = Price(fiat="eur", days_ago=1)
        price_instance.set_days_ago(7)
        self.assertEqual(price_instance.days_ago, 7)


if __name__ == "__main__":
    unittest.main()
