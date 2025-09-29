from datetime import datetime
def log(event: str, **kv):
    ts = datetime.utcnow().isoformat()
    print(f"{ts} {event} {kv}")

