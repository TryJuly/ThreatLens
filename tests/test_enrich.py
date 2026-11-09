from unittest.mock import MagicMock

from geoip2.errors import AddressNotFoundError

from enrich.enrich import enrich_once, get_new_ips, lookup_ip

#   —— get_new_ips ——

def test_get_new_ips():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [("1.1.1.1",), ("2.2.2.2",)]

    assert get_new_ips(mock_conn) == ["1.1.1.1", "2.2.2.2"]


#   —— lookup_ip ——

def test_lookup_ip_found():
    city_reader = MagicMock()
    city_reader.city.return_value.country.iso_code = "US"
    city_reader.city.return_value.city.name = "Mountain View"
    city_reader.city.return_value.location.latitude = 37.4
    city_reader.city.return_value.location.longitude = -122.0

    asn_reader = MagicMock()
    asn_reader.asn.return_value.autonomous_system_number = 15169
    asn_reader.asn.return_value.autonomous_system_organization = "Google LLC"

    info = lookup_ip(city_reader, asn_reader, "8.8.8.8")

    assert info == {
        "country": "US", "city": "Mountain View", "latitude": 37.4, "longitude": -122.0,
        "asn": 15169, "org": "Google LLC",
    }

def test_lookup_ip_not_found():
    city_reader = MagicMock()
    city_reader.city.side_effect = AddressNotFoundError("not found")

    asn_reader = MagicMock()
    asn_reader.asn.side_effect = AddressNotFoundError("not found")

    info = lookup_ip(city_reader, asn_reader, "10.0.0.1")

    assert info == {
        "country": None, "city": None, "latitude": None, "longitude": None,
        "asn": None, "org": None,
    }


#   —— enrich_once ——

def test_enrich_once_no_new_ip(monkeypatch):
    monkeypatch.setattr("enrich.enrich.get_new_ips", lambda conn: [])

    assert enrich_once(MagicMock(), MagicMock(), MagicMock()) == 0

def test_enrich_once_inserts(monkeypatch):
    monkeypatch.setattr("enrich.enrich.get_new_ips", lambda conn: ["8.8.8.8"])
    monkeypatch.setattr(
        "enrich.enrich.lookup_ip",
        lambda city_reader, asn_reader, ip: {
            "country": "US", "city": "Mountain View", "latitude": 37.4, "longitude": -122.0,
            "asn": 15169, "org": "Google LLC",
        },
    )

    mock_conn = MagicMock()
    assert enrich_once(mock_conn, MagicMock(), MagicMock()) == 1

    rows = mock_conn.cursor.return_value.__enter__.return_value.executemany.call_args[0][1]
    assert rows == [("8.8.8.8", "US", "Mountain View", 37.4, -122.0, 15169, "Google LLC")]
