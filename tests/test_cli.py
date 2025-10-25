from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from btcpriceticker import _version
from btcpriceticker.cli import app, main, state


class TestCLI:
    def setup_method(self):
        state["verbose"] = 3
        state["service"] = "mempool"
        self.runner = CliRunner()

    def test_version_module_exposes_metadata(self):
        assert isinstance(_version.__version__, str)
        assert isinstance(_version.version_tuple, tuple)

    def test_main_updates_state(self):
        main(verbose=1, service="kraken")

        assert state["verbose"] == 1
        assert state["service"] == "kraken"

    def test_price_command_uses_state_service(self):
        with patch("btcpriceticker.cli.Price") as mock_price:
            mock_instance = mock_price.return_value
            mock_instance.get_price_now.return_value = "123"

            result = self.runner.invoke(app, ["price", "eur"])

            assert result.exit_code == 0
            mock_price.assert_called_once_with(
                service="mempool",
                fiat="eur",
                enable_ohlc=False,
                enable_timeseries=False,
                enable_ohlcv=False,
            )
            assert "123" in result.stdout

    def test_history_command_prints_timeseries(self):
        with patch("btcpriceticker.cli.Price") as mock_price:
            mock_instance = mock_price.return_value
            mock_instance.timeseries = MagicMock()
            mock_instance.timeseries.data = "history-data"

            result = self.runner.invoke(app, ["history", "usd", "1h"])

            assert result.exit_code == 0
            assert "history-data" in result.stdout

    def test_ohlc_and_ohlcv_commands_use_flags(self):
        with patch("btcpriceticker.cli.Price") as mock_price:
            price_instance = mock_price.return_value
            price_instance.ohlc = "ohlc-data"
            price_instance.ohlcv = "ohlcv-data"

            result_ohlc = self.runner.invoke(app, ["ohlc", "usd", "1h"])
            result_ohlcv = self.runner.invoke(app, ["ohlcv", "usd", "1h"])

            assert result_ohlc.exit_code == 0
            assert result_ohlcv.exit_code == 0

            ohlc_call = mock_price.call_args_list[-2]
            ohlcv_call = mock_price.call_args_list[-1]

            assert ohlc_call.kwargs["enable_ohlc"] is True
            assert ohlc_call.kwargs["enable_ohlcv"] is False
            assert ohlcv_call.kwargs["enable_ohlc"] is False
            assert ohlcv_call.kwargs["enable_ohlcv"] is True

            assert "ohlc-data" in result_ohlc.stdout
            assert "ohlcv-data" in result_ohlcv.stdout

    def test_cli_arguments_update_state_before_commands(self):
        with patch("btcpriceticker.cli.Price") as mock_price:
            mock_price.return_value.get_price_now.return_value = "456"

            result = self.runner.invoke(
                app,
                ["--service", "kraken", "--verbose", "0", "price", "usd"],
            )

            assert result.exit_code == 0
            mock_price.assert_called_with(
                service="kraken",
                fiat="usd",
                enable_ohlc=False,
                enable_timeseries=False,
                enable_ohlcv=False,
            )
            assert state["service"] == "kraken"
