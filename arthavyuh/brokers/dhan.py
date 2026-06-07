"""Read-only DhanHQ data bridge.

This module intentionally exposes only data-ingestion endpoints. It does not
contain order placement, modification, cancellation, or position conversion code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from arthavyuh.core.config import DEFAULT_OHLCV_DIR, resolve_path
from arthavyuh.core.exceptions import ConfigError

DHAN_BASE_URL = "https://api.dhan.co/v2"
DEFAULT_DHAN_INSTRUMENTS_PATH = Path("config/dhan_instruments_sample.csv")


@dataclass(frozen=True)
class DhanCredentials:
    client_id: str
    access_token: str

    @classmethod
    def from_env(cls) -> "DhanCredentials":
        client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
        access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
        missing = []
        if not client_id:
            missing.append("DHAN_CLIENT_ID")
        if not access_token:
            missing.append("DHAN_ACCESS_TOKEN")
        if missing:
            raise ConfigError(f"Missing Dhan environment variables: {', '.join(missing)}")
        return cls(client_id=client_id, access_token=access_token)


class DhanReadOnlyClient:
    """Small REST client for DhanHQ read-only endpoints."""

    def __init__(
        self,
        credentials: DhanCredentials | None = None,
        base_url: str = DHAN_BASE_URL,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.credentials = credentials or DhanCredentials.from_env()
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def _headers(self, include_client_id: bool = False) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "access-token": self.credentials.access_token,
        }
        if include_client_id:
            headers["client-id"] = self.credentials.client_id
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        include_client_id: bool = False,
    ) -> Any:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(include_client_id=include_client_id),
            params=params,
            json=json_body,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            body = response.text[:500]
            raise RuntimeError(f"DhanHQ API request failed: {response.status_code} {body}") from exc
        if not response.content:
            return None
        return response.json()

    def profile(self) -> dict[str, Any]:
        return self._request("GET", "/profile")

    def holdings(self) -> list[dict[str, Any]]:
        return self._request("GET", "/holdings")

    def positions(self) -> list[dict[str, Any]]:
        return self._request("GET", "/positions")

    def ledger(self, from_date: str, to_date: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "/ledger",
            params={"from-date": from_date, "to-date": to_date},
        )

    def trades(self, from_date: str, to_date: str, page: int = 0) -> list[dict[str, Any]]:
        return self._request("GET", f"/trades/{from_date}/{to_date}/{page}")

    def market_ltp(self, instruments: dict[str, list[int]]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/marketfeed/ltp",
            json_body=instruments,
            include_client_id=True,
        )

    def market_ohlc(self, instruments: dict[str, list[int]]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/marketfeed/ohlc",
            json_body=instruments,
            include_client_id=True,
        )

    def market_quote(self, instruments: dict[str, list[int]]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/marketfeed/quote",
            json_body=instruments,
            include_client_id=True,
        )

    def historical_daily(
        self,
        *,
        security_id: str,
        exchange_segment: str,
        instrument: str,
        from_date: str,
        to_date: str,
        expiry_code: int = 0,
        include_oi: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/charts/historical",
            json_body={
                "securityId": str(security_id),
                "exchangeSegment": exchange_segment,
                "instrument": instrument,
                "expiryCode": expiry_code,
                "oi": include_oi,
                "fromDate": from_date,
                "toDate": to_date,
            },
        )


def load_dhan_instruments(path: str | Path = DEFAULT_DHAN_INSTRUMENTS_PATH) -> list[dict[str, str]]:
    resolved = resolve_path(path)
    if not resolved.exists():
        raise ConfigError(f"Dhan instruments file not found: {resolved}")
    df = pd.read_csv(resolved, dtype=str).fillna("")
    required = {"symbol", "security_id", "exchange_segment", "instrument"}
    missing = required.difference(df.columns)
    if missing:
        raise ConfigError(f"Dhan instruments file missing columns: {', '.join(sorted(missing))}")
    return df[["symbol", "security_id", "exchange_segment", "instrument"]].to_dict(orient="records")


def instruments_to_marketfeed_payload(instruments: list[dict[str, str]]) -> dict[str, list[int]]:
    payload: dict[str, list[int]] = {}
    for item in instruments:
        segment = item["exchange_segment"]
        payload.setdefault(segment, []).append(int(item["security_id"]))
    return payload


def historical_response_to_ohlcv(response: dict[str, Any]) -> pd.DataFrame:
    timestamps = response.get("timestamp", [])
    data = {
        "date": pd.to_datetime(timestamps, unit="s", utc=True)
        .tz_convert("Asia/Kolkata")
        .date.astype(str),
        "open": response.get("open", []),
        "high": response.get("high", []),
        "low": response.get("low", []),
        "close": response.get("close", []),
        "volume": response.get("volume", []),
    }
    df = pd.DataFrame(data)
    if df.empty:
        return df
    return df[["date", "open", "high", "low", "close", "volume"]]


def write_historical_ohlcv_csv(
    symbol: str,
    response: dict[str, Any],
    output_dir: str | Path = DEFAULT_OHLCV_DIR,
) -> Path:
    df = historical_response_to_ohlcv(response)
    resolved_dir = resolve_path(output_dir)
    resolved_dir.mkdir(parents=True, exist_ok=True)
    output_path = resolved_dir / f"{symbol}.csv"
    df.to_csv(output_path, index=False)
    return output_path
