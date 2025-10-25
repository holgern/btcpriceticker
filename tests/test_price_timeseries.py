from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from btcpriceticker.price_timeseries import PriceTimeSeries


class TestPriceTimeSeries:
    def setup_method(self):
        self.series = PriceTimeSeries()

    def test_add_price_and_get_price_list_with_days_filter(self):
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=2)
        recent_timestamp = datetime.now(timezone.utc)

        self.series.add_price(old_timestamp, 100.0)
        self.series.add_price(recent_timestamp, 200.0)

        all_prices = self.series.get_price_list()
        filtered_prices = self.series.get_price_list(days=1)

        assert all_prices == [100.0, 200.0]
        assert filtered_prices == [200.0]

    def test_get_timestamp_list_filters_by_days(self):
        old_timestamp = datetime.now(timezone.utc) - timedelta(days=3)
        recent_timestamp = datetime.now(timezone.utc)

        self.series.add_price(old_timestamp, 100.0)
        self.series.add_price(recent_timestamp, 200.0)

        timestamps = self.series.get_timestamp_list(days=1)

        assert len(timestamps) == 1
        assert isinstance(timestamps[0], float)

    def test_append_dataframe_combines_and_sorts(self):
        base_time = datetime.now(timezone.utc)
        self.series.add_price(base_time, 100.0)

        other_df = pd.DataFrame(
            {
                "timestamp": [
                    base_time - timedelta(hours=1),
                    base_time + timedelta(hours=1),
                ],
                "price": [90.0, 110.0],
            }
        )

        self.series.append_dataframe(other_df)

        prices = self.series.get_price_list()
        assert prices == [90.0, 100.0, 110.0]

    def test_append_dataframe_invalid_columns_raises(self):
        with pytest.raises(ValueError, match="must contain 'timestamp' and 'price'"):
            self.series.append_dataframe(pd.DataFrame({"foo": [1], "bar": [2]}))

    def test_get_percentage_change(self):
        base_time = datetime.now(timezone.utc)
        self.series.add_price(base_time - timedelta(days=1), 100.0)
        self.series.add_price(base_time, 110.0)

        change = self.series.get_percentage_change(days=2)

        assert change == pytest.approx(10.0)

    def test_get_percentage_change_returns_none_when_insufficient_data(self):
        change = self.series.get_percentage_change(days=1)

        assert change is None

    def test_resample_to_ohlcv(self):
        base_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        self.series.add_price(base_time, 100.0)
        self.series.add_price(base_time + timedelta(minutes=10), 105.0)
        self.series.add_price(base_time + timedelta(minutes=20), 95.0)
        self.series.add_price(base_time + timedelta(hours=1), 120.0)

        ohlcv = self.series.resample_to_ohlcv("1h")

        assert list(ohlcv.columns) == ["Open", "High", "Low", "Close", "Volume"]
        assert len(ohlcv) == 2

        first_row = ohlcv.iloc[0]
        assert first_row["Open"] == 100.0
        assert first_row["High"] == 105.0
        assert first_row["Low"] == 95.0
        assert first_row["Close"] == 95.0
        assert first_row["Volume"] == 3

    def test_resample_to_ohlcv_empty(self):
        result = self.series.resample_to_ohlcv("1h")

        assert result.empty
