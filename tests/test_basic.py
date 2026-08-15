import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200


def test_login_get(client):
    r = client.get('/login')
    assert r.status_code == 200


def test_register_get(client):
    r = client.get('/register')
    assert r.status_code == 200


def test_token_requires_login(client):
    r = client.get('/api/token')
    assert r.status_code in (302, 401)
