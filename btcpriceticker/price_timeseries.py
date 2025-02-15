from datetime import datetime, timedelta

import pandas as pd


class PriceTimeSeries:
    def __init__(self):
        self.data = pd.DataFrame(columns=["timestamp", "price"])

    def add_price(self, timestamp: datetime, price: float):
        """Add a new price point to the time series."""
        new_data = pd.DataFrame([[timestamp, price]], columns=["timestamp", "price"])
        if not self.data.empty:
            self.data = pd.concat([self.data, new_data], ignore_index=True)
        else:
            self.data = new_data.reset_index(drop=True)

    def get_price_list(self, days: int = None):
        """Return the time series as a list of (timestamp, price) tuples,
        optionally filtered by the last `days` days."""
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            filtered_data = self.data[self.data["timestamp"] >= cutoff]
        else:
            filtered_data = self.data
        return filtered_data.loc[:, "price"].values.tolist()

    def get_timestamp_list(self, days: int = None):
        """Return the time series as a list of (timestamp, price) tuples,
        optionally filtered by the last `days` days."""
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            filtered_data = self.data[self.data["timestamp"] >= cutoff]
        else:
            filtered_data = self.data
        return (filtered_data["timestamp"].astype("int64") / 1e9).values.tolist()

    def get_data(self, days: int = None):
        """Return the time series as a Pandas DataFrame,
        optionally filtered by the last `days` days."""
        if days is not None:
            cutoff = datetime.now() - timedelta(days=days)
            return self.data[self.data["timestamp"] >= cutoff]
        return self.data

    def append_dataframe(self, other_df: pd.DataFrame):
        """Append another dataframe containing timestamp
        and price columns to the time series."""
        if not {"timestamp", "price"}.issubset(other_df.columns):
            raise ValueError("DataFrame must contain 'timestamp' and 'price' columns")
        if other_df.empty:
            return
        if not self.data.empty:
            self.data = pd.concat([self.data, other_df], ignore_index=True)
        else:
            self.data = other_df.reset_index(drop=True)
        self.data = self.data.sort_values(by="timestamp").reset_index(drop=True)

    def get_percentage_change(self, days: int):
        """Return the percentage change in price from the past `days` days to now."""
        cutoff = datetime.now() - timedelta(days=days)
        past_data = self.data[self.data["timestamp"] >= cutoff]
        if past_data.empty:
            return None
        past_price = past_data.iloc[0]["price"]
        current_price = self.data.iloc[-1]["price"]
        return ((current_price - past_price) / past_price) * 100 if past_price else None

    def resample_to_ohlc(self, time_frame: str) -> pd.DataFrame:
        """
        Convert a dataframe with timestamp and price into an OHLC chart.

        Parameters:
            time_frame (str): Pandas-compatible resampling
            period (e.g., '1h', '1d', '15t')

        Returns:
            pd.DataFrame: DataFrame with columns ["Open", "High", "Low", "Close"]
        """
        df = self.data.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("time", inplace=True)

        ohlc_df = df["price"].resample(time_frame).ohlc()

        return ohlc_df
