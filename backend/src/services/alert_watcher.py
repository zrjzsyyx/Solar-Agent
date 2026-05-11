import asyncio
import logging

from src.agent.graphs.alert_graph import alert_graph
from src.config import settings
from src.services.data_backend_client import backend

logger = logging.getLogger(__name__)

_processed: set[int] = set()


async def poll_and_process():
    """每 N 秒轮询一次数据后端的 OPEN 告警，发现新告警就送入 LangGraph 处理。"""
    interval = settings.alert_poll_interval_sec
    logger.info(f"Alert watcher started, poll every {interval}s")

    while True:
        try:
            resp = await backend.list_alerts(status="OPEN", limit=50)
            for alert in resp.data.items:
                if alert.id in _processed:
                    continue

                logger.info(
                    f"New alert #{alert.id}: {alert.station_name} "
                    f"{alert.inverter_sn} str#{alert.string_index} "
                    f"{alert.severity} {alert.deviation_pct}%"
                )

                state = {
                    "alert_id": alert.id,
                    "station_name": alert.station_name,
                    "inverter_sn": alert.inverter_sn,
                    "string_index": alert.string_index,
                    "severity": alert.severity,
                    "deviation_pct": alert.deviation_pct,
                    "description": alert.description or "",
                    "raw_context": alert.raw_context or "",
                    "messages": [],
                }

                try:
                    result = await alert_graph.ainvoke(state)
                    analysis = result.get("analysis", "")
                    suggestion = result.get("suggestion", "")
                    logger.info(f"Alert #{alert.id} processed: {suggestion[:100]}...")
                except Exception as e:
                    logger.error(f"Alert #{alert.id} graph failed: {e}")

                _processed.add(alert.id)

        except Exception as e:
            logger.error(f"Alert poll error: {e}")

        await asyncio.sleep(interval)
