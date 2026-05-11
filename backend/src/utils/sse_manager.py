import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(self):
        self._queues: dict[int, asyncio.Queue] = {}
        self._counter = 0

    def connect(self) -> tuple[int, asyncio.Queue]:
        self._counter += 1
        cid = self._counter
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues[cid] = q
        logger.info(f"SSE client {cid} connected, total={len(self._queues)}")
        return cid, q

    def disconnect(self, cid: int):
        self._queues.pop(cid, None)
        logger.info(f"SSE client {cid} disconnected, total={len(self._queues)}")

    async def broadcast(self, event_type: str, data: dict):
        payload = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        payload_str = json.dumps(payload, ensure_ascii=False)
        stale: list[int] = []
        for cid, q in self._queues.items():
            try:
                q.put_nowait(payload_str)
            except asyncio.QueueFull:
                stale.append(cid)
        for cid in stale:
            self.disconnect(cid)

    async def broadcast_alert(self, alert_data: dict):
        await self.broadcast("alert", alert_data)

    @property
    def client_count(self) -> int:
        return len(self._queues)


sse_manager = SSEManager()
