from unittest.mock import MagicMock

from analysis.report import fetch_summary, print_summary

#   —— fetch_summary ——

def test_fetch_summary():
    mock_conn = MagicMock()
    cur = mock_conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [("1.1.1.1", 3, "US", "Mountain View", "Google LLC")]

    rows = fetch_summary(mock_conn, 20)

    assert rows == [("1.1.1.1", 3, "US", "Mountain View", "Google LLC")]
    assert cur.execute.call_args[0][1] == (20,)

#   —— print_summary ——

def test_print_summary(capsys):
    rows = [
        ("1.1.1.1", 3, "US", "Mountain View", "Google LLC"),
        ("2.2.2.2", 1, None, None, None),
    ]

    print_summary(rows)

    out = capsys.readouterr().out
    assert "1.1.1.1" in out
    assert "Google LLC" in out
    assert "?" in out  # IP sans géoloc connue
