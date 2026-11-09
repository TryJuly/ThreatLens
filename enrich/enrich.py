import os
import time

import geoip2.database
import psycopg
from geoip2.errors import AddressNotFoundError

DATABASE_URL = os.environ["DATABASE_URL"]
CITY_DB_PATH = os.environ.get("CITY_DB_PATH", "data/dbip-city-lite-2026-11.mmdb")
ASN_DB_PATH = os.environ.get("ASN_DB_PATH", "data/dbip-asn-lite-2026-11.mmdb")
INTERVAL = int(os.environ.get("ENRICH_INTERVAL", "60"))

# IPs déjà vues dans events mais absentes de ip_info
def get_new_ips(conn: psycopg.Connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT DISTINCT e.src_ip FROM events e
               LEFT JOIN ip_info i ON i.ip = e.src_ip
               WHERE i.ip IS NULL"""
        )
        return [row[0] for row in cur.fetchall()]

# interroge les bases city + asn pour une IP, renvoie les colonnes de ip_info (sauf abuse_score)
def lookup_ip(city_reader: geoip2.database.Reader, asn_reader: geoip2.database.Reader, ip: str) -> dict:
    result = {"country": None, "city": None, "latitude": None, "longitude": None, "asn": None, "org": None}

    try:
        city = city_reader.city(ip)
        result["country"] = city.country.iso_code
        result["city"] = city.city.name
        result["latitude"] = city.location.latitude
        result["longitude"] = city.location.longitude
    except AddressNotFoundError:
        pass

    try:
        asn = asn_reader.asn(ip)
        result["asn"] = asn.autonomous_system_number
        result["org"] = asn.autonomous_system_organization
    except AddressNotFoundError:
        pass

    return result

# enrichit les nouvelles IPs et les insère dans ip_info, renvoie le nombre d'IPs traitées
def enrich_once(conn: psycopg.Connection, city_reader: geoip2.database.Reader, asn_reader: geoip2.database.Reader) -> int:
    ips = get_new_ips(conn)
    if not ips:
        return 0

    rows = []
    for ip in ips:
        info = lookup_ip(city_reader, asn_reader, ip)
        rows.append((ip, info["country"], info["city"], info["latitude"], info["longitude"], info["asn"], info["org"]))

    with conn.transaction(), conn.cursor() as cur:
        cur.executemany(
            """INSERT INTO ip_info (ip, country, city, latitude, longitude, asn, org, checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, now())
               ON CONFLICT (ip) DO NOTHING""",
            rows,
        )
    return len(rows)

# boucle principale : se connecte à la base et aux bases GeoIP, lance enrich_once toutes les INTERVAL secondes
def main() -> None:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn, \
         geoip2.database.Reader(CITY_DB_PATH) as city_reader, \
         geoip2.database.Reader(ASN_DB_PATH) as asn_reader:
        print(f"Enrichissement démarré (toutes les {INTERVAL} s)")
        while True:
            n = enrich_once(conn, city_reader, asn_reader)
            if n:
                print(f"{n} IP(s) enrichie(s)")
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
