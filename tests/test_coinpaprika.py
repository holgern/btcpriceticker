import unittest
from unittest.mock import patch

from btcpriceticker.coinpaprika import CoinPaprika


class TestCoinpaprika(unittest.TestCase):
    @patch("coinpaprika.client.Client.ticker")
    def test_get_current_price(self, mock_for_coin):
        mock_for_coin.return_value = {"quotes": {"USD": {"price": 50000}}}

        cp = CoinPaprika("USD", whichcoin="btc-bitcoin")
        price = cp.get_current_price("USD")
        self.assertEqual(price, 50000)

    @patch("coinpaprika.client.Client.exchange_markets")
    def test_get_exchange_usd_price(self, mock_markets):
        mock_markets.return_value = [
            {"pair": "BTC/USDC", "quotes": {"USD": {"price": 50000}}}
        ]

        cp = CoinPaprika("USD", whichcoin="btc-bitcoin")
        price = cp.get_exchange_usd_price("binance", "BTC/USDC")
        self.assertEqual(price, 50000)


if __name__ == "__main__":
    unittest.main()
