'''
SafeWalk app
Name: Areeba Haroon
Course project: SP25-CPSC-49200-004
Semester: Spring 2025
'''


from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///safewalk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(128))

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    description = db.Column(db.String(255))
    date = db.Column(db.String(50))

class Walk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    path_data = db.Column(db.Text)  # Store as JSON string

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        user = User(name=name, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password, user.password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists('safewalk.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)

