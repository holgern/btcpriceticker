import logging

logger = logging.getLogger(__name__)

COINPAPRIKA_MODULE = None
try:
    from coinpaprika import client as Coinpaprika

    COINPAPRIKA_MODULE = "coinpaprika"
except ImportError:
    pass


class CoinPaprika:
    def __init__(self, whichcoin="btc-bitcoin", hours_ago=2):
        self.api_client = Coinpaprika.Client() if COINPAPRIKA_MODULE else None
        self.whichcoin = whichcoin
        self.hours_ago = hours_ago
        self.coins = None

    def get_coin(self, name=None, symbol=None):
        if self.coins is None:
            self.coins = self.api_client.coins()
        for coin in self.coins:
            if name and coin["name"] == name:
                return coin
            if symbol and coin["symbol"] == symbol:
                return coin
        return False

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Coinpaprika."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.ticker(self.whichcoin, quotes=currency)
            return float(ticker["quotes"][currency]["price"])
        except Exception as e:
            logger.exception(f"Failed to fetch current price: {e}")
            return None

    def get_exchange_usd_price(self, exchange, pair, currency="USD"):
        """Fetch the USD price for a given exchange and pair."""
        if not self.api_client:
            return None
        try:
            markets = self.api_client.exchange_markets(exchange, quotes=currency)
            for market in markets:
                if market["pair"] == pair:
                    return float(market["quotes"][currency]["price"])
            logger.info("Not USD, could not get price.")
            return None
        except Exception as e:
            logger.exception(f"Failed to fetch exchange USD price: {e}")
            return None
