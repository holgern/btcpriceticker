import unittest
from unittest.mock import patch

from btcpriceticker.mempool import Mempool


class TestMempool(unittest.TestCase):
    @patch("pymempool.MempoolAPI.get_price")
    def test_get_current_price(self, mock_for_coin):
        mock_for_coin.return_value = {"USD": 50000}

        m = Mempool("USD")
        price = m.get_current_price("USD")
        self.assertEqual(price, 50000)


if __name__ == "__main__":
    unittest.main()
