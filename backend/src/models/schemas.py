from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Alert ──────────────────────────────────────────────

class AlertItem(BaseModel):
    """对应 GET /api/alerts 返回的 items 元素"""
    id: int
    station_id: int
    station_name: str
    inverter_sn: str
    string_index: int
    severity: Literal["WARNING", "CRITICAL"]
    status: Literal["OPEN", "ACKED", "CLOSED", "RECOVERED"]
    voltage: float
    reference_voltage: float
    deviation_pct: float
    threshold_pct: float
    started_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    dedup_key: Optional[str] = None
    description: Optional[str] = None
    raw_context: Optional[str] = None
    operator_note: Optional[str] = None


class AlertListData(BaseModel):
    total: int
    page: int
    limit: int
    items: list[AlertItem]


class AlertListResponse(BaseModel):
    success: bool
    data: AlertListData


class AlertDetailResponse(BaseModel):
    success: bool
    data: AlertItem


class AckResponse(BaseModel):
    success: bool
    data: dict


class ClosePayload(BaseModel):
    operator_note: Optional[str] = None


# ── Inverter ───────────────────────────────────────────

class InverterLatestData(BaseModel):
    time: Optional[str] = None
    state: Optional[int] = None
    pac: Optional[float] = None
    power: Optional[float] = None
    dc_input_type: Optional[int] = None
    payload: Optional[str] = None


class InverterLatestResponse(BaseModel):
    success: bool
    data: InverterLatestData


class TrendPoint(BaseModel):
    time: Optional[str] = None
    voltage: Optional[float] = None
    reference_voltage: Optional[float] = None
    deviation_pct: Optional[float] = None


class InverterTrendResponse(BaseModel):
    success: bool
    data: list[TrendPoint]


# ── Station ────────────────────────────────────────────

class LatestAlertBrief(BaseModel):
    id: int
    station_id: int
    station_name: str
    inverter_sn: str
    string_index: int
    severity: str
    status: str
    voltage: float
    reference_voltage: float
    deviation_pct: float
    threshold_pct: float
    started_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    description: Optional[str] = None
    raw_context: Optional[str] = None


class StationStatusData(BaseModel):
    station_id: int
    online_device_count: int
    open_alert_count: int
    latest_alerts: list[LatestAlertBrief] = []


class StationStatusResponse(BaseModel):
    success: bool
    data: StationStatusData


# ── Agent API ──────────────────────────────────────────

class QARequest(BaseModel):
    question: str
    station_id: Optional[int] = None
    inverter_sn: Optional[str] = None


class QAResponse(BaseModel):
    answer: str
    intent: str = ""
    tools_called: list[str] = []
    error: Optional[str] = None


class ReportRequest(BaseModel):
    report_type: Literal["weekly", "monthly"] = "weekly"
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    report_markdown: str
    error: Optional[str] = None


# ── SSE ────────────────────────────────────────────────

class SSEAlertPayload(BaseModel):
    alert_id: int
    station_id: int
    station_name: str
    inverter_sn: str
    string_index: int
    severity: str
    deviation_pct: float
    description: str
    suggestion: str = ""
    analysis: str = ""
