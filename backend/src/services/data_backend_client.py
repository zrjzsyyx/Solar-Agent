import logging
from typing import Optional

import httpx

from src.config import settings
from src.models.schemas import (
    AlertDetailResponse,
    AlertListResponse,
    ClosePayload,
    InverterLatestResponse,
    InverterTrendResponse,
    StationStatusResponse,
)

logger = logging.getLogger(__name__)


class DataBackendClient:
    def __init__(self):
        self.base = settings.data_backend_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    def _build_url(self, path: str) -> str:
        return f"{self.base}{path}"

    async def health(self) -> dict:
        client = await self._get_client()
        resp = await client.get(self._build_url("/health"))
        return resp.json()

    # ── Alerts ───────────────────────────────────────

    async def list_alerts(
        self,
        station_id: Optional[int] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AlertListResponse:
        client = await self._get_client()
        params = {"limit": limit, "offset": offset}
        if station_id:
            params["station_id"] = station_id
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        resp = await client.get(self._build_url("/api/alerts"), params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Backend error: {data.get('detail', 'unknown')}")
        return AlertListResponse(**data)

    async def get_alert(self, alert_id: int) -> AlertDetailResponse:
        client = await self._get_client()
        resp = await client.get(self._build_url(f"/api/alerts/{alert_id}"))
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Backend error: {data.get('detail', 'unknown')}")
        return AlertDetailResponse(**data)

    async def ack_alert(self, alert_id: int) -> dict:
        client = await self._get_client()
        resp = await client.post(self._build_url(f"/api/alerts/{alert_id}/ack"))
        resp.raise_for_status()
        return resp.json()

    async def close_alert(self, alert_id: int, note: str = "") -> dict:
        client = await self._get_client()
        payload = ClosePayload(operator_note=note)
        resp = await client.post(
            self._build_url(f"/api/alerts/{alert_id}/close"),
            json=payload.model_dump(exclude_none=True),
        )
        resp.raise_for_status()
        return resp.json()

    # ── Inverters ────────────────────────────────────

    async def get_inverter_latest(self, sn: str) -> InverterLatestResponse:
        client = await self._get_client()
        resp = await client.get(self._build_url(f"/api/inverters/{sn}/latest"))
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Backend error: {data.get('detail', 'unknown')}")
        return InverterLatestResponse(**data)

    async def get_inverter_trend(
        self,
        sn: str,
        string_index: int,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> InverterTrendResponse:
        client = await self._get_client()
        params = {"string_index": string_index}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        resp = await client.get(
            self._build_url(f"/api/inverters/{sn}/trend"), params=params
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Backend error: {data.get('detail', 'unknown')}")
        return InverterTrendResponse(**data)

    # ── Stations ─────────────────────────────────────

    async def get_station_status(self, station_id: int) -> StationStatusResponse:
        client = await self._get_client()
        resp = await client.get(
            self._build_url(f"/api/stations/{station_id}/status")
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Backend error: {data.get('detail', 'unknown')}")
        return StationStatusResponse(**data)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


backend = DataBackendClient()
