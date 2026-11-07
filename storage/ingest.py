import json, os, time
import psycopg
from psycopg.types.json import Jsonb

LOG_PATH = os.environ.get("LOG_PATH", "data/events.jsonl")
OFFSET_PATH = os.environ.get("OFFSET_PATH", "data/ingest.offset")
DATABASE_URL = os.environ["DATABASE_URL"]
INTERVAL = int(os.environ.get("INGEST_INTERVAL", "30"))

# champs qui ont leur propre colonne ; tout le reste part dans "data" (JSONB)
COLUMNS = ("ts", "sensor", "event", "src_ip", "src_port", "username", "password")

def read_offset():
    try:
        with open(OFFSET_PATH) as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

def write_offset(offset):
    tmp = OFFSET_PATH + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(offset))
    os.replace(tmp, OFFSET_PATH)  # remplacement atomique

def to_row(event):
    row = tuple(event.pop(col, None) for col in COLUMNS)
    return row + (Jsonb(event),)

def read_new_events(offset):
    if os.path.getsize(LOG_PATH) < offset:
        offset = 0  # le fichier a été vidé ou remplacé (rotation des logs)
    rows = []
    with open(LOG_PATH, "rb") as f:
        f.seek(offset)
        for line in f:
            if not line.endswith(b"\n"):
                break  # ligne incomplète : le capteur est en train de l'écrire
            offset += len(line)
            try:
                rows.append(to_row(json.loads(line)))
            except json.JSONDecodeError:
                print(f"Ligne invalide ignorée (offset {offset})")
    return rows, offset

def ingest_once(conn):
    if not os.path.exists(LOG_PATH):
        return 0
    rows, new_offset = read_new_events(read_offset())
    if rows:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO events
                       (ts, sensor, event, src_ip, src_port, username, password, data)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    rows,
                )
    write_offset(new_offset)
    return len(rows)

def main():
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        print(f"Ingestion démarrée (toutes les {INTERVAL} s)")
        while True:
            n = ingest_once(conn)
            if n:
                print(f"{n} événement(s) inséré(s)")
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()