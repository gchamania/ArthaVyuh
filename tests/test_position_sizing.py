from arthavyuh.risk.position_sizing import calculate_position_size


def test_position_sizing_valid_case() -> None:
    result = calculate_position_size(
        capital=100000,
        risk_percent=1,
        entry=500,
        stop_loss=475,
    )

    assert result.valid is True
    assert result.quantity == 40
    assert result.risk_amount == 1000
    assert result.capital_required == 20000


def test_position_sizing_invalid_stop_loss() -> None:
    result = calculate_position_size(
        capital=100000,
        risk_percent=1,
        entry=500,
        stop_loss=505,
    )

    assert result.valid is False
    assert result.quantity == 0
    assert "below entry" in result.reason
