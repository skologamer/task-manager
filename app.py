from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from icalendar import Calendar
from io import BytesIO
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_urlsafe(16))

db = SQLAlchemy(app)
# Allow CORS for API access from packaged apps or external origins.
CORS(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    remind_before = db.Column(db.Integer, default=15)  # minutes
    notify = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_notified = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed': self.completed,
            'remind_before': self.remind_before,
            'notify': self.notify,
            'created_at': self.created_at.isoformat()
            ,'user_id': self.user_id
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET', 'POST'])
def tasks_route():
    # Identify user by token or session
    user = None
    auth = request.headers.get('Authorization')
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ',1)[1]
        user = User.query.filter_by(api_token=token).first()
    if not user and current_user and current_user.is_authenticated:
        user = current_user

    if request.method == 'GET':
        if user:
            tasks = Task.query.filter_by(user_id=user.id).order_by(Task.due_date.asc().nulls_last()).all()
        else:
            tasks = Task.query.filter_by(user_id=None).order_by(Task.due_date.asc().nulls_last()).all()
        return jsonify([t.to_dict() for t in tasks])

    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title required'}), 400
    due = data.get('due_date')
    due_dt = None
    if due:
        try:
            due_dt = datetime.fromisoformat(due)
        except Exception:
            due_dt = None
    task = Task(
        title=title,
        description=data.get('description'),
        due_date=due_dt,
        remind_before=int(data.get('remind_before', 15)),
        notify=bool(data.get('notify', True))
    )
    if user:
        task.user_id = user.id
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
def task_modify(task_id):
    task = Task.query.get_or_404(task_id)
    # identify user
    user = None
    auth = request.headers.get('Authorization')
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ',1)[1]
        user = User.query.filter_by(api_token=token).first()
    if not user and current_user and current_user.is_authenticated:
        user = current_user
    # enforce ownership if task is owned
    if task.user_id and (not user or task.user_id != user.id):
        return jsonify({'error': 'forbidden'}), 403
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return '', 204
    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    due = data.get('due_date')
    if due is not None:
        try:
            task.due_date = datetime.fromisoformat(due) if due else None
        except Exception:
            pass
    task.completed = bool(data.get('completed', task.completed))
    task.remind_before = int(data.get('remind_before', task.remind_before))
    task.notify = bool(data.get('notify', task.notify))
    db.session.commit()
    return jsonify(task.to_dict())


@app.route('/api/import_ics', methods=['POST'])
def import_ics():
    if 'ics' not in request.files:
        return jsonify({'error': 'no file uploaded'}), 400
    f = request.files['ics']
    try:
        cal = Calendar.from_ical(f.read())
    except Exception:
        return jsonify({'error': 'invalid ics file'}), 400
    created = 0
    # identify user for import (token or session)
    user = None
    auth = request.headers.get('Authorization')
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ',1)[1]
        user = User.query.filter_by(api_token=token).first()
    if not user and current_user and current_user.is_authenticated:
        user = current_user

    for component in cal.walk():
        if component.name == 'VEVENT':
            title = str(component.get('summary', 'Untitled'))
            dt = component.get('dtstart')
            due_dt = None
            if dt:
                try:
                    due_dt = dt.dt
                    if isinstance(due_dt, datetime):
                        pass
                    else:
                        # if date only, convert to datetime at midnight
                        due_dt = datetime.combine(due_dt, datetime.min.time())
                except Exception:
                    due_dt = None
            task = Task(title=title, description=str(component.get('description', '')), due_date=due_dt)
            if user:
                task.user_id = user.id
            db.session.add(task)
            created += 1
    db.session.commit()
    return jsonify({'imported': created})


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50), nullable=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    api_token = db.Column(db.String(200), unique=True, nullable=True)
    tasks = db.relationship('Task', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route('/api/register_token', methods=['POST'])
def register_token():
    data = request.get_json() or {}
    token = data.get('token')
    platform = data.get('platform')
    if not token:
        return jsonify({'error': 'token required'}), 400
    d = Device.query.filter_by(token=token).first()
    if not d:
        d = Device(token=token, platform=platform)
        db.session.add(d)
        db.session.commit()
    return jsonify({'status': 'ok'})


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    data = request.form
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        flash('Username and password required', 'error')
        return redirect(url_for('register'))
    if User.query.filter_by(username=username).first():
        flash('Username already taken', 'error')
        return redirect(url_for('register'))
    if len(password) < 8:
        flash('Password must be at least 8 characters', 'error')
        return redirect(url_for('register'))
    u = User(username=username)
    u.set_password(password)
    u.api_token = secrets.token_urlsafe(32)
    db.session.add(u)
    db.session.commit()
    login_user(u)
    flash('Account created', 'success')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.form
    username = data.get('username')
    password = data.get('password')
    u = User.query.filter_by(username=username).first()
    if not u or not u.check_password(password):
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))
    login_user(u)
    flash('Logged in', 'success')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'GET':
        return render_template('account.html')
    # POST: change password
    old = request.form.get('old_password')
    new = request.form.get('new_password')
    if not old or not new:
        flash('Old and new password required', 'error')
        return redirect(url_for('account'))
    u = current_user
    if not u.check_password(old):
        flash('Invalid current password', 'error')
        return redirect(url_for('account'))
    if len(new) < 8:
        flash('New password must be at least 8 characters', 'error')
        return redirect(url_for('account'))
    if old == new:
        flash('New password must be different', 'error')
        return redirect(url_for('account'))
    u.set_password(new)
    db.session.commit()
    flash('Password changed', 'success')
    return redirect(url_for('account'))


@app.route('/account/regenerate', methods=['POST'])
@login_required
def account_regenerate():
    u = current_user
    u.api_token = secrets.token_urlsafe(32)
    db.session.commit()
    flash('API token regenerated', 'success')
    return redirect(url_for('account'))


@app.route('/api/token', methods=['GET'])
@login_required
def get_token():
    u = current_user
    if not u.api_token:
        u.api_token = secrets.token_urlsafe(32)
        db.session.commit()
    return jsonify({'token': u.api_token})


def send_push_via_fcm(token, title, body):
    key = os.environ.get('FCM_SERVER_KEY')
    if not key:
        app.logger.debug('FCM_SERVER_KEY not set; skipping push')
        return False
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {'Authorization': 'key=' + key, 'Content-Type': 'application/json'}
    payload = {
        'to': token,
        'notification': {'title': title, 'body': body},
        'priority': 'high'
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        app.logger.debug('FCM response %s', r.text)
        return r.status_code == 200
    except Exception as e:
        app.logger.exception('FCM send failed')
        return False


def check_and_send_reminders():
    now = datetime.utcnow()
    soon = now
    later = now
    # Find tasks that are not completed, have due_date, notify enabled, and haven't been notified yet
    tasks = Task.query.filter(Task.completed == False, Task.due_date.isnot(None), Task.notify == True).all()
    for t in tasks:
        if not t.due_date:
            continue
        notify_delta = timedelta(minutes=(t.remind_before or 15))
        notify_time = t.due_date - notify_delta
        # If notify_time is within the last minute and we haven't notified already
        if notify_time <= now <= notify_time + timedelta(seconds=59):
            if t.last_notified and t.last_notified >= notify_time:
                continue
            # send to all registered devices
            devices = Device.query.all()
            for d in devices:
                send_push_via_fcm(d.token, 'Task Reminder: ' + t.title, t.description or '')
            t.last_notified = now
            db.session.add(t)
    db.session.commit()


from datetime import timedelta

scheduler = BackgroundScheduler()
# Do not start the background scheduler while running tests
if not app.config.get('TESTING', False):
    scheduler.add_job(func=check_and_send_reminders, trigger='interval', seconds=60, id='reminder_job')
    scheduler.start()

if __name__ == '__main__':
    if not os.path.exists('tasks.db'):
        db.create_all()
    app.run(debug=True)
