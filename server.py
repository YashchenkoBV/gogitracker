from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime, date


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


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task_text = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="In Progress", nullable=False)  # New status field


# Create tables if they don't exist
with app.app_context():
    db.create_all()


def is_past(year, month, day):
    return date(year, month, day) < date.today()


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
    Главная страница с календарем и списком ближайших задач.
    """
    if not current_user():
        return render_template("welcome.html")

    user = current_user()
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    # Календарь текущего месяца
    cal = calendar.Calendar(firstweekday=0)  # Понедельник = 0
    month_days = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Фильтрация задач: показываем только "In Progress" и будущие задачи
    upcoming_tasks = (
        Task.query
        .filter(Task.user_id == user.id, Task.date >= now.date(), Task.status == "In Progress")
        .order_by(Task.date)
        .limit(10)  # Показываем до 10 задач
        .all()
    )

    # Добавляем количество оставшихся дней для каждой задачи
    for task in upcoming_tasks:
        task.days_left = (task.date - now.date()).days + 1

    return render_template(
        "index.html",
        current_user=user,
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days,
        upcoming_tasks=upcoming_tasks,
        is_past=lambda y, m, d: datetime(y, m, d).date() < now.date()  # Передаем в шаблон проверку прошедших дат
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
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="This username is already taken"
            )

        # Validate password
        if len(password) < 8:
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="Password must be at least 8 characters long"
            )

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Redirect to the login page instead of the main page
        return redirect(url_for('login'))

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
        if not user or not check_password_hash(user.password_hash, password):
            return render_template(
                'login.html',
                current_user=current_user(),
                error_message="Invalid username or password"
            )

        # Log in the user
        session['user_id'] = user.id
        return redirect(url_for('index'))

    return render_template('login.html', current_user=current_user())


@app.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
def tasks(year, month, day):
    """
    Page for adding, viewing, and updating tasks for a specific date.
    Includes task status management.
    """
    if not current_user():
        return redirect(url_for('login'))

    user = current_user()
    date = datetime(year, month, day).date()

    if request.method == 'POST':
        if 'task' in request.form:  # Add a new task
            task_text = request.form.get('task')
            if task_text:
                new_task = Task(user_id=user.id, date=date, task_text=task_text)
                db.session.add(new_task)
                db.session.commit()
        elif 'task_id' in request.form:  # Update task status to "Done"
            task_id = request.form.get('task_id')
            task = Task.query.filter_by(id=task_id, user_id=user.id).first()
            if task:
                task.status = "Done"
                db.session.commit()

        return redirect(url_for('tasks', year=year, month=month, day=day))

    # Retrieve tasks categorized by status
    tasks_in_progress = Task.query.filter_by(user_id=user.id, date=date, status="In Progress").all()
    done_tasks = Task.query.filter_by(user_id=user.id, date=date, status="Done").all()

    return render_template(
        'tasks.html',
        year=year,
        month=month,
        day=day,
        tasks_in_progress=tasks_in_progress,
        done_tasks=done_tasks
    )


@app.route('/mark_finished', methods=['POST'])
def mark_finished():
    task_id = request.form.get('task_id')
    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        task.status = "Done"
        db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
