import pytest
from unittest.mock import patch, MagicMock
from rule_engine import isCreated_DB, Insert_DB


@pytest.fixture
def mock_db():
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        yield mock_conn, mock_cursor


def test_isCreated_DB_table_exists(mock_db):
    mock_conn, mock_cursor = mock_db
    mock_cursor.fetchone.return_value = (True,)  # Таблица существует

    isCreated_DB()

    mock_cursor.execute.assert_called_once_with(
        'SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s) AS table_exists;',
        ('route',)
    )

def test_Insert_DB(mock_db):
    mock_conn, mock_cursor = mock_db
    test_data = [('1000', '50', '85213', '25', '52', '52', '2025-05-23 13:19:09.771370')]

    Insert_DB(test_data)

    mock_cursor.execute.assert_called_with(
        "INSERT INTO \troute (DEVICE_ID, SITEID, UPNOM, PUTNOM, LON, LAT, TIMESTP) VALUES (%s, %s, %s, %s, %s, %s, %s);",
        ('1000', '50', '85213', '25', '52', '52', '2025-05-23 13:19:09.771370')
    )
    mock_conn.commit.assert_called_once()