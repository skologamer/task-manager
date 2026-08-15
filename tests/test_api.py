import json
import secrets
import pytest
from app import app, db, User, Device


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def create_user():
    u = User(username='testuser')
    u.set_password('password123')
    u.api_token = secrets.token_urlsafe(32)
    db.session.add(u)
    db.session.commit()
    return u


def test_crud_task(client):
    with app.app_context():
        u = create_user()
        headers = {'Authorization': 'Bearer ' + u.api_token, 'Content-Type': 'application/json'}
        # create
        rv = client.post('/api/tasks', data=json.dumps({'title': 'Buy milk'}), headers=headers)
        assert rv.status_code == 201
        task = rv.get_json()
        tid = task['id']
        # list
        rv = client.get('/api/tasks', headers=headers)
        assert rv.status_code == 200
        tasks = rv.get_json()
        assert any(t['id'] == tid for t in tasks)
        # update
        rv = client.put(f'/api/tasks/{tid}', data=json.dumps({'title': 'Buy bread'}), headers=headers)
        assert rv.status_code == 200
        assert rv.get_json()['title'] == 'Buy bread'
        # delete
        rv = client.delete(f'/api/tasks/{tid}', headers=headers)
        assert rv.status_code == 204


def test_register_token(client):
    with app.app_context():
        rv = client.post('/api/register_token', json={'token': 'tkn123', 'platform': 'android'})
        assert rv.status_code == 200
        assert rv.get_json().get('status') == 'ok'
