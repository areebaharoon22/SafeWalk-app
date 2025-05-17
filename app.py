'''
SafeWalk app
Name: Areeba Haroon
Course project: SP25-CPSC-49200-004
Semester: Spring 2025
'''


from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt
import os
import json
from flask_mail import Mail, Message


app = Flask(__name__)
# Email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hennaservicebyareeba@gmail.com'        # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'autn qjqr wchd cysu'           # Replace with app-specific password

mail = Mail(app)

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

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))


# Routes
@app.route('/')
def login_landing():
    return redirect(url_for('login'))

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

@app.route('/save-walk', methods=['POST'])
def save_walk():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = session['user_id']
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    path = data.get('path')

    walk = Walk(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        path_data=json.dumps(path)
    )
    db.session.add(walk)
    db.session.commit()

    return jsonify({'message': 'Walk saved successfully'})


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    from datetime import datetime, timezone
    import json

    # Pagination
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    # Query 1 extra to determine if there's a next page
    all_walks = Walk.query.filter_by(user_id=session['user_id'])\
        .order_by(Walk.start_time.desc())\
        .offset(offset).limit(per_page + 1).all()

    walks = all_walks[:per_page]
    has_more = len(all_walks) > per_page

    local_zone = datetime.now().astimezone().tzinfo
    walk_summaries = []

    for walk in walks:
        try:
            path = json.loads(walk.path_data)
            start_point = path[0] if path else None
            end_point = path[-1] if path else None

            # Convert ISO UTC to local time
            start_time_obj = datetime.fromisoformat(walk.start_time.replace('Z', '')).replace(tzinfo=timezone.utc).astimezone(local_zone)
            end_time_obj = datetime.fromisoformat(walk.end_time.replace('Z', '')).replace(tzinfo=timezone.utc).astimezone(local_zone)

            duration = max(1, int((end_time_obj - start_time_obj).total_seconds() // 60))
            steps = duration * 120

            walk_summaries.append({
                'date': start_time_obj.strftime("%B %d, %Y"),
                'start_time': start_time_obj.strftime("%I:%M:%S %p"),
                'end_time': end_time_obj.strftime("%I:%M:%S %p"),
                'duration': duration,
                'steps': steps,
                'start_location': f"{start_point['latitude']:.5f}, {start_point['longitude']:.5f}" if start_point else "Unknown",
                'end_location': f"{end_point['latitude']:.5f}, {end_point['longitude']:.5f}" if end_point else "Unknown",
            })
        except:
            walk_summaries.append({
                'date': "Error",
                'start_time': walk.start_time,
                'end_time': walk.end_time,
                'duration': 0,
                'steps': 0,
                'start_location': "Error",
                'end_location': "Error"
            })

    return render_template("history.html", walks=walk_summaries, page=page, has_more=has_more)

@app.route('/contacts', methods=['GET'])
def contacts():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    contacts = Contact.query.filter_by(user_id=user_id).all()
    return render_template('contacts.html', contacts=contacts)

@app.route('/add-contact', methods=['POST'])
def add_contact():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    name = request.form['name']
    email = request.form['email']
    user_id = session['user_id']
    contact = Contact(user_id=user_id, name=name, email=email)
    db.session.add(contact)
    db.session.commit()
    return redirect(url_for('contacts'))

@app.route('/delete-contact/<int:id>')
def delete_contact(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    contact = Contact.query.get_or_404(id)
    if contact.user_id == session['user_id']:
        db.session.delete(contact)
        db.session.commit()
    return redirect(url_for('contacts'))

@app.route('/send-alert', methods=['POST'])
def send_alert():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    location = data.get('location')  # should be a "lat,lon" string

    user_id = session['user_id']
    contacts = Contact.query.filter_by(user_id=user_id).all()

    if not contacts:
        return jsonify({'error': 'No contacts to notify'}), 400

    map_link = f"https://www.google.com/maps?q={location}"

    subject = "🚨 SafeWalk Alert - Location Shared"
    body = f"""
Hi,

Your contact just sent an alert from SafeWalk.

They are currently here:
{map_link}

Please check in with them.

— SafeWalk Notification
"""

    for contact in contacts:
        msg = Message(subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[contact.email])
        msg.body = body
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email to {contact.email}: {e}")

    return jsonify({'message': 'Alert email sent to trusted contacts!'})


if __name__ == '__main__':
    if not os.path.exists('safewalk.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
