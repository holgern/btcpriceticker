import unittest
from unittest.mock import patch

from btcpriceticker.coingecko import CoinGecko


class TestCoinGecko(unittest.TestCase):
    @patch("btcpriceticker.coingecko.CoinGeckoAPI.get_coins_markets")
    def test_get_current_price(self, mock_get_coins_markets):
        mock_get_coins_markets.return_value = [{"current_price": 50000}]

        cg = CoinGecko("usd", whichcoin="bitcoin")
        price = cg.get_current_price("usd")
        self.assertEqual(price, 50000)

    @patch("btcpriceticker.coingecko.CoinGeckoAPI.get_exchanges_tickers_by_id")
    def test_get_exchange_usd_price(self, mock_get_exchanges_tickers_by_id):
        mock_get_exchanges_tickers_by_id.return_value = {
            "tickers": [{"target": "USD", "last": 50000}]
        }

        cg = CoinGecko("usd", whichcoin="bitcoin")
        price = cg.get_exchange_usd_price("binance")
        self.assertEqual(price, 50000)

    @patch("btcpriceticker.coingecko.CoinGeckoAPI.get_coin_market_chart_by_id")
    @patch("btcpriceticker.coingecko.CoinGecko.get_current_price")
    def test_get_history_price(
        self, mock_get_current_price, mock_get_coin_market_chart_by_id
    ):
        mock_get_coin_market_chart_by_id.return_value = {
            "prices": [[1609459200000, 40000], [1609545600000, 50000.0]]
        }
        mock_get_current_price.return_value = 50000.0

        cg = CoinGecko("usd", whichcoin="bitcoin", days_ago=1)
        history = cg.get_history_price("usd")
        self.assertEqual(
            history, {"prices": [[1609459200000, 40000], [1609545600000, 50000.0]]}
        )


if __name__ == "__main__":
    unittest.main()
