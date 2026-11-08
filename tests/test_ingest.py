from storage.ingest import to_row
from storage.ingest import read_offset
from storage.ingest import write_offset
from storage.ingest import read_new_events
from storage.ingest import ingest_once

from psycopg.types.json import Jsonb
from unittest.mock import MagicMock


#   —— to_row ——

def test_to_row():
    data = {
        "ts": "2024-06-01T12:00:00Z", "sensor": "sensor1", "event": "login", "src_ip": "10.10.10.10", "username": "hacker", "password": "1234",
    }
    row = to_row(data)

    assert row[:7] == (
        "2024-06-01T12:00:00Z", "sensor1", "login", "10.10.10.10", None, "hacker", "1234",
        ), "Les colonnes connues doivent être dans le bon ordre"

    assert isinstance(row[7], Jsonb), "Le dernier élément doit être un Jsonb"

    data = {}
    row = to_row(data)

    assert row[:7] == (
        None, None, None, None, None, None, None,
    )

    data = {
        "Salut": "Bonjour", "foo": "bar"
    }
    row = to_row(data)

    assert row[-1].obj == {"Salut": "Bonjour", "foo": "bar"}, "Le JSONB doit contenir les champs restants"

#   —— read_offset ——

def test_read_offset(tmp_path):
    file = tmp_path / "test_offset.txt"
    file.write_text("42")

    assert read_offset(file) == 42, "L'offset doit être lu correctement"

    file.write_text("")

    assert read_offset(file) == 0

#   —— write_offset ——

def test_write_offset(tmp_path):
    file = tmp_path / "test_offset.txt"

    write_offset(42, str(file))

    assert file.read_text() == "42"

#   —— read_new_events ——

def test_read_new_events(tmp_path):
    file = tmp_path / "test_events.jsonl"
    file.write_text('{"ts": "2024-06-01T12:00:00Z", "sensor": "sensor1", "event": "login"}\n')

    rows, offset = read_new_events(0, str(file))
    print(rows[0][:-1])

    assert rows[0][:-1] == ("2024-06-01T12:00:00Z", "sensor1", "login", None, None, None, None)
    assert isinstance(rows[0][-1], Jsonb)
    assert offset == file.stat().st_size, "L'offset doit être mis à jour correctement"

#   —— ingest_once ——

def test_ingest_once(tmp_path):

    assert ingest_once(None, "error", None) == 0, "Si le fichier de log n'existe pas, on ne fait rien et on retourne 0"

    mock_conn = MagicMock()
    file = tmp_path / "test_events.txt"
    offset = tmp_path / "offset.txt"

    file.write_text('{"ts": "2024-06-01T12:00:00Z", "sensor": "sensor1", "event": "login"}\n')
    offset.write_text("0")

    assert ingest_once(mock_conn, str(file), str(offset)) == 1
    check = mock_conn.cursor.return_value.__enter__.return_value.executemany.call_args[0][1][0]
    assert check[:-1] == ("2024-06-01T12:00:00Z", "sensor1", "login", None, None, None, None)

    file.write_text('{"ts": "2024-06-01T12:00:00Z", "sensor": "sensor1", "event": "login"}')

    assert ingest_once(mock_conn, str(file), str(offset)) == 0
    assert mock_conn.cursor.return_value.__enter__.return_value.executemany.call_count == 1, "On ne doit pas insérer de ligne si le fichier est incomplet"

