import json

import redis

from app.core.config import get_settings

REDIS_CHANNEL = "snapshot_updates"


def publish_snapshot_update(host_id: str, snapshot_id: str, collected_at: str) -> None:
    client = redis.from_url(get_settings().redis_url)
    client.publish(
        REDIS_CHANNEL,
        json.dumps(
            {
                "type": "snapshot:update",
                "host_id": host_id,
                "snapshot_id": snapshot_id,
                "collected_at": collected_at,
            }
        ),
    )
