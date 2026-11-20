from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.main import app


def make_client(mock_conn):
    app.state.conn = mock_conn
    return TestClient(app)


#   —— /health ——

def test_health():
    client = make_client(MagicMock())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


#   —— /events ——

def test_events_returns_rows():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [
        {
            "id": 1, "ts": "2026-11-20T10:00:00", "sensor": "ssh_honeypot", "event": "connect",
            "src_ip": "1.2.3.4", "src_port": 1234, "username": None, "password": None, "data": {},
        }
    ]

    client = make_client(mock_conn)
    response = client.get("/events")

    assert response.status_code == 200
    assert response.json()[0]["src_ip"] == "1.2.3.4"

def test_events_rejects_invalid_ip():
    client = make_client(MagicMock())

    response = client.get("/events", params={"src_ip": "not-an-ip"})

    assert response.status_code == 422


#   —— /ips/{ip} ——

def test_ip_info_not_found():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = None

    client = make_client(mock_conn)
    response = client.get("/ips/8.8.8.8")

    assert response.status_code == 404

def test_ip_info_found():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchone.return_value = {
        "ip": "8.8.8.8", "country": "US", "city": "Mountain View",
        "latitude": 37.4, "longitude": -122.0, "asn": 15169,
        "org": "Google LLC", "abuse_score": None, "checked_at": None,
    }

    client = make_client(mock_conn)
    response = client.get("/ips/8.8.8.8")

    assert response.status_code == 200
    assert response.json()["country"] == "US"

def test_ip_info_rejects_invalid_ip():
    client = make_client(MagicMock())

    response = client.get("/ips/not-an-ip")

    assert response.status_code == 422


#   —— /stats ——

def test_stats():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchall.side_effect = [
        [("ssh_honeypot", 10)],
        [("connect", 7), ("login_attempt", 3)],
        [("1.2.3.4", 5)],
    ]

    client = make_client(mock_conn)
    response = client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {
        "by_sensor": {"ssh_honeypot": 10},
        "by_event": {"connect": 7, "login_attempt": 3},
        "top_ips": [{"src_ip": "1.2.3.4", "count": 5}],
    }
