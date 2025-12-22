from datetime import datetime, timezone
import uuid

def now_ms():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_id():
    return str(uuid.uuid4())