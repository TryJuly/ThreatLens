import json, os, datetime

LOG_PATH = os.environ.get("LOG_PATH", "data/events.jsonl")

def log_event(**fields):
    fields["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(fields, ensure_ascii=False) + "\n")