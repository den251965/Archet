import pytest
from unittest.mock import patch, MagicMock
from server_rule import app, jsoncreat
import json


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_jsoncreat():
    result = jsoncreat(0)
    assert result[0]['status'] == 'ok'


def test_get_endpoint(client):
    test_data = {
            "device_id": 500,
            "lon": 50,
            "lat": 20,
            "siteid": 1,
            "upnom": '14500',
            "putnom": '25',
            "time": '2025-05-23 13:19:09.771370'
    }

    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data[0]['status'] == 'ok'


def test_post_endpoint(client):
    test_data = {
            "device_id": 500,
            "lon": 50,
            "lat": 20,
            "siteid": 1,
            "upnom": '14500',
            "putnom": '25',
            "time": '2025-05-23 13:19:09.771370'
    }

    response = client.post(
        '/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    assert response.status_code == 200