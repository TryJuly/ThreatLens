import json
import os
import time

import psycopg
from psycopg.types.json import Jsonb

LOG_PATH = os.environ.get("LOG_PATH", "data/events.jsonl")
OFFSET_PATH = os.environ.get("OFFSET_PATH", "data/ingest.offset")
DATABASE_URL = os.environ["DATABASE_URL"]
INTERVAL = int(os.environ.get("INGEST_INTERVAL", "30"))

# champs qui ont leur propre colonne ; tout le reste part dans "data" (JSONB)
COLUMNS = ("ts", "sensor", "event", "src_ip", "src_port", "username", "password")

# lit le dernier offset traité depuis le fichier OFFSET_PATH (0 si absent)
def read_offset(path: str) -> int:
    try:
        with open(path) as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

# sauvegarde l'offset traité dans OFFSET_PATH
def write_offset(offset: str, path: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(offset))
    os.replace(tmp, path)  # remplacement atomique

# transforme un event (dict) en tuple prêt pour l'INSERT : colonnes connues en premier, le reste en JSONB
def to_row(event: dict) -> tuple:
    row = tuple(event.pop(col, None) for col in COLUMNS)
    return row + (Jsonb(event),)

# lit les nouvelles lignes du fichier de log à partir de offset, renvoie (rows, nouvel offset)
def read_new_events(offset: str, log_path: str) -> tuple[list[tuple], int]:
    if os.path.getsize(log_path) < offset:
        offset = 0  # le fichier a été vidé ou remplacé (rotation des logs)
    rows = []
    with open(log_path, "rb") as f:
        f.seek(offset)
        for line in f:
            if not line.endswith(b"\n"):
                break  # ligne incomplète : le capteur est en train de l'écrire
            error = offset
            offset += len(line)
            try:
                rows.append(to_row(json.loads(line)))
            except json.JSONDecodeError:
                print(f"Ligne invalide ignorée (offset {error})")
    return rows, offset

# lit les events non encore traités et les insère en base (une ligne invalide est ignorée sans bloquer les autres), puis avance l'offset
def ingest_once(conn: psycopg.Connection, log_path: str, offset_path: str) -> int:
    if not os.path.exists(log_path):
        return 0
    rows, new_offset = read_new_events(read_offset(offset_path), log_path)
    inserted = 0
    for row in rows:
        try:
            with conn.transaction(), conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO events
                           (ts, sensor, event, src_ip, src_port, username, password, data)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    row,
                )
            inserted += 1
        except psycopg.Error as e:
            print(f"Événement invalide ignoré : {e}")
    write_offset(new_offset, offset_path)
    return inserted

# boucle principale : se connecte à la base et lance ingest_once toutes les INTERVAL secondes
def main() -> None:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        print(f"Ingestion démarrée (toutes les {INTERVAL} s)")
        while True:
            n = ingest_once(conn, LOG_PATH, OFFSET_PATH)
            if n:
                print(f"{n} événement(s) inséré(s)")
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()