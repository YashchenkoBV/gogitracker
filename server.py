from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = "YOUR_SECRET_KEY_HERE"  # Replace with a secure key in production

# Configure SQLAlchemy (using SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ Database Model ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# ------------------ Helper Functions ------------------
def current_user():
    """
    Utility to check if someone is logged in (by user_id in session).
    Returns the User object if logged in, or None if not.
    """
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# ------------------ Routes ------------------

@app.route('/')
def index():
    """
    Calendar view (main page).
    If user is logged in, we can show tasks later; for now, we just show the calendar.
    """
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    cal = calendar.Calendar(firstweekday=0)  # Monday=0, Sunday=6
    month_days = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    return render_template(
        "index.html",
        current_user=current_user(),
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    Sign Up page. Displays a form to register a new user.
    On POST, creates the user in the database if username is not taken.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists. Please choose another one.", 400

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Automatically sign in the user after registration
        session['user_id'] = new_user.id
        return redirect(url_for('index'))

    return render_template('signup.html', current_user=current_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Sign In page. Displays a form to log in.
    On POST, checks credentials and logs user in if correct.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return "Invalid username or password.", 400

    return render_template('login.html', current_user=current_user())

@app.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
