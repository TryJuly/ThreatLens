import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
TOP_N = int(os.environ.get("REPORT_TOP_N", "20"))

# top IPs par nombre de tentatives, avec leur géoloc si connue
def fetch_summary(conn: psycopg.Connection, limit: int) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT e.src_ip, count(*) AS attempts, i.country, i.city, i.org
               FROM events e
               LEFT JOIN ip_info i ON i.ip = e.src_ip
               GROUP BY e.src_ip, i.country, i.city, i.org
               ORDER BY attempts DESC
               LIMIT %s""",
            (limit,),
        )
        return cur.fetchall()

# affiche le résumé dans le terminal, une ligne par IP
def print_summary(rows: list[tuple]) -> None:
    print(f"{'IP':<17} {'Tentatives':<11} {'Pays':<6} {'Ville':<25} Organisation")
    for src_ip, attempts, country, city, org in rows:
        print(f"{src_ip!s:<17} {attempts:<11} {country or '?':<6} {city or '?':<25} {org or '?'}")

def main() -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        rows = fetch_summary(conn, TOP_N)
        print_summary(rows)

if __name__ == "__main__":
    main()
