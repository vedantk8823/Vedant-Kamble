from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------- Models ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    membership_type = db.Column(db.String(50))
    contact_info = db.Column(db.String(100))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship('Client', backref=db.backref('attendances', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- Routes ----------------
@app.route('/')
@login_required
def dashboard():
    total_clients = Client.query.count()
    today = datetime.today().date()
    today_attendance = Attendance.query.filter(db.func.date(Attendance.timestamp) == today).count()
    attendance_history = Attendance.query.order_by(Attendance.timestamp.desc()).limit(10).all()
    return render_template('dashboard.html', total_clients=total_clients, today_attendance=today_attendance, attendance_history=attendance_history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        membership_type = request.form['membership_type']
        contact_info = request.form['contact_info']
        client = Client(name=name, age=age, membership_type=membership_type, contact_info=contact_info)
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully')
        return redirect(url_for('view_clients'))
    return render_template('add_client.html')

@app.route('/view_clients')
@login_required
def view_clients():
    clients = Client.query.all()
    return render_template('view_clients.html', clients=clients)

@app.route('/delete_client/<int:id>')
@login_required
def delete_client(id):
    client = Client.query.get(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted')
    return redirect(url_for('view_clients'))

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    clients = Client.query.all()
    if request.method == 'POST':
        client_id = request.form['client_id']
        attendance = Attendance(client_id=client_id)
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance marked')
        return redirect(url_for('dashboard'))
    return render_template('mark_attendance.html', clients=clients)

@app.route('/view_attendance')
@login_required
def view_attendance():
    attendance_list = Attendance.query.order_by(Attendance.timestamp.desc()).all()
    return render_template('view_attendance.html', attendance_list=attendance_list)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
