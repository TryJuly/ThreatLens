import psycopg
from psycopg.rows import dict_row


# liste les events les plus récents, filtrables par IP/sensor/event
def list_events(
    conn: psycopg.Connection,
    limit: int,
    offset: int,
    src_ip: str | None = None,
    sensor: str | None = None,
    event: str | None = None,
) -> list[dict]:
    conditions = []
    params: list = []
    if src_ip is not None:
        conditions.append("src_ip = %s")
        params.append(src_ip)
    if sensor is not None:
        conditions.append("sensor = %s")
        params.append(sensor)
    if event is not None:
        conditions.append("event = %s")
        params.append(event)

    query = "SELECT id, ts, sensor, event, src_ip, src_port, username, password, data FROM events"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY ts DESC LIMIT %s OFFSET %s"
    params += [limit, offset]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


# renvoie les infos GeoIP/ASN d'une IP, ou None si jamais enrichie
def get_ip_info(conn: psycopg.Connection, ip: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """SELECT ip, country, city, latitude, longitude, asn, org, abuse_score, checked_at
               FROM ip_info WHERE ip = %s""",
            (ip,),
        )
        return cur.fetchone()


# compteurs globaux : events par capteur, par type, et top 10 des IPs les plus actives
def get_stats(conn: psycopg.Connection) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT sensor, count(*) FROM events GROUP BY sensor")
        by_sensor = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT event, count(*) FROM events GROUP BY event")
        by_event = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute(
            """SELECT src_ip, count(*) AS n FROM events
               GROUP BY src_ip ORDER BY n DESC LIMIT 10"""
        )
        top_ips = [{"src_ip": str(ip), "count": n} for ip, n in cur.fetchall()]

    return {"by_sensor": by_sensor, "by_event": by_event, "top_ips": top_ips}
