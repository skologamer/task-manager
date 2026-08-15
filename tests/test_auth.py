import io
import pytest
from app import app, db, User, Task


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_register_and_login(client):
    # register
    rv = client.post('/register', data={'username': 'alice', 'password': 'password123'}, follow_redirects=True)
    assert rv.status_code == 200
    # login should succeed
    rv = client.post('/login', data={'username': 'alice', 'password': 'password123'}, follow_redirects=True)
    assert rv.status_code == 200


def test_import_ics_creates_task(client):
    with app.app_context():
        ics = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20260101T100000Z
END:VEVENT
END:VCALENDAR
"""
        data = {
            'ics': (io.BytesIO(ics), 'test.ics')
        }
        rv = client.post('/api/import_ics', data=data, content_type='multipart/form-data')
        assert rv.status_code == 200
        assert rv.get_json().get('imported', 0) >= 1
