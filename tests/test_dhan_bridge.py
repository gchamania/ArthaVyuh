from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from arthavyuh.brokers.dhan import (
    DhanCredentials,
    DhanReadOnlyClient,
    historical_response_to_ohlcv,
    instruments_to_marketfeed_payload,
    load_dhan_instruments,
    write_historical_ohlcv_csv,
)
from arthavyuh.core.exceptions import ConfigError
from arthavyuh.database.repository import save_broker_snapshot


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.text = str(payload)
        self.content = b"{}"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("request failed")

    def json(self) -> Any:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse({"ok": True})


def test_dhan_credentials_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DHAN_CLIENT_ID", "client")
    monkeypatch.setenv("DHAN_ACCESS_TOKEN", "token")

    credentials = DhanCredentials.from_env()

    assert credentials.client_id == "client"
    assert credentials.access_token == "token"


def test_dhan_credentials_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DHAN_CLIENT_ID", raising=False)
    monkeypatch.delenv("DHAN_ACCESS_TOKEN", raising=False)

    with pytest.raises(ConfigError):
        DhanCredentials.from_env()


def test_dhan_client_uses_read_only_headers() -> None:
    session = FakeSession()
    client = DhanReadOnlyClient(
        credentials=DhanCredentials(client_id="client", access_token="token"),
        session=session,  # type: ignore[arg-type]
    )

    client.ledger("2026-06-01", "2026-06-07")
    client.market_ltp({"NSE_EQ": [2885]})

    ledger_call = session.calls[0]
    ltp_call = session.calls[1]
    assert ledger_call["method"] == "GET"
    assert ledger_call["url"].endswith("/ledger")
    assert ledger_call["headers"]["access-token"] == "token"
    assert "client-id" not in ledger_call["headers"]
    assert ltp_call["method"] == "POST"
    assert ltp_call["url"].endswith("/marketfeed/ltp")
    assert ltp_call["headers"]["client-id"] == "client"


def test_load_dhan_instruments_and_payload(tmp_path: Path) -> None:
    path = tmp_path / "instruments.csv"
    path.write_text(
        "symbol,security_id,exchange_segment,instrument\n"
        "RELIANCE,2885,NSE_EQ,EQUITY\n"
        "TCS,11536,NSE_EQ,EQUITY\n",
        encoding="utf-8",
    )

    instruments = load_dhan_instruments(path)
    payload = instruments_to_marketfeed_payload(instruments)

    assert instruments[0]["symbol"] == "RELIANCE"
    assert payload == {"NSE_EQ": [2885, 11536]}


def test_historical_response_writes_ohlcv(tmp_path: Path) -> None:
    response = {
        "timestamp": [1735689600, 1735776000],
        "open": [100, 101],
        "high": [105, 106],
        "low": [99, 100],
        "close": [104, 105],
        "volume": [1000, 1100],
    }

    df = historical_response_to_ohlcv(response)
    output = write_historical_ohlcv_csv("RELIANCE", response, tmp_path)
    saved = pd.read_csv(output)

    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert output.name == "RELIANCE.csv"
    assert saved["close"].tolist() == [104, 105]


def test_save_broker_snapshot(tmp_path: Path) -> None:
    snapshot_id = save_broker_snapshot(
        "dhan",
        "ledger",
        [{"amount": 10}],
        from_date="2026-06-01",
        to_date="2026-06-07",
        db_path=tmp_path / "arthavyuh.db",
    )

    assert snapshot_id == 1
