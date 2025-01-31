import logging

logger = logging.getLogger(__name__)

MEMPOOL_MODULE = None
try:
    from pymempool.api import MempoolAPI

    MEMPOOL_MODULE = "pymempool"
except ImportError:
    pass


class Mempool:
    def __init__(self, hours_ago=2):
        self.api_client = MempoolAPI() if MEMPOOL_MODULE else None
        self.hours_ago = hours_ago

    def get_current_price(self, currency="USD"):
        """Fetch the current price from Mempool."""
        if not self.api_client:
            return None
        try:
            ticker = self.api_client.get_price()
            return float(ticker[currency])
        except Exception as e:
            logger.exception(f"Failed to fetch current price: {e}")
            return None
