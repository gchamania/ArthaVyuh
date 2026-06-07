from arthavyuh.data.loader import load_ohlcv
from arthavyuh.strategies.registry import default_registry


def test_builtin_strategies_return_signal_or_none_without_crashing() -> None:
    df = load_ohlcv("DEMO_RELIANCE")
    registry = default_registry()

    for strategy in registry.list_strategies():
        signal = strategy.run("DEMO_RELIANCE", df, {"strategies": {}})
        assert signal is None or signal.symbol == "DEMO_RELIANCE"
