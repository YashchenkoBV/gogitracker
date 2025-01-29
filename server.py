from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime, date
from authlib.integrations.flask_client import OAuth
import base64
import re


app = Flask(__name__)
app.config.from_pyfile('keys/config.py')
app.secret_key = app.config['SECRET_KEY']

# Configure SQLAlchemy (using SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

oauth = OAuth(app)

# GitHub OAuth registration (dynamic credentials will be used)
github = oauth.register(
    name='github',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'repo'},
)


# ------------------ Database Model ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    github_client_id = db.Column(db.String(255), nullable=True)  # GitHub client ID
    github_client_secret = db.Column(db.String(255), nullable=True)  # GitHub client secret
    github_token = db.Column(db.String(255), nullable=True)  # OAuth token


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    task_text = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="In Progress", nullable=False)


# Create tables if they don't exist
with app.app_context():
    db.create_all()


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
def is_past(year, month, day):
    return date(year, month, day) < date.today()


@app.route('/')
def index():
    if not current_user():
        return render_template("welcome.html")

    user = current_user()
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    month_days = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Check if the user wants to view done tasks
    show_done_tasks = request.args.get("show_done", "false").lower() == "true"
    task_status = "Done" if show_done_tasks else "In Progress"

    # Fetch tasks grouped by date based on selected status
    tasks_by_date = {}

    if show_done_tasks:
        tasks = (
            Task.query.filter(Task.user_id == user.id, Task.status == "Done")
            .order_by(Task.date.desc(), Task.id.desc())  # Order by most recently finished
            .all()
        )
    else:
        tasks = Task.query.filter(Task.user_id == user.id, Task.status == "In Progress").all()

    for task in tasks:
        date_key = task.date.strftime("%Y-%m-%d")
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        if len(tasks_by_date[date_key]) < 3:  # Show up to 3 tasks per date
            tasks_by_date[date_key].append(task.task_text[:10] + "..." if len(task.task_text) > 10 else task.task_text)

    # ✅ Ensure upcoming tasks are always shown, even when viewing done tasks
    upcoming_tasks = (
        Task.query
        .filter(Task.user_id == user.id, Task.date >= now.date(), Task.status == "In Progress")
        .order_by(Task.date)
        .limit(10)
        .all()
    )

    for task in upcoming_tasks:
        task.days_left = (task.date - now.date()).days

    return render_template(
        "index.html",
        current_user=user,
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days,
        tasks_by_date=tasks_by_date,  # ✅ Ensures done tasks appear for past dates
        upcoming_tasks=upcoming_tasks,
        is_past=is_past,
        now=now,
        show_done_tasks=show_done_tasks
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
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    show_done_tasks = request.args.get("show_done", "false").lower() == "true"

    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        task.status = "Done"
        db.session.commit()

    return redirect(url_for('index', year=year, month=month, show_done=show_done_tasks))



@app.route('/link-github', methods=['GET', 'POST'])
def link_github():
    """
    Allows the user to input their GitHub OAuth client ID and secret.
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    if request.method == 'POST':
        github_client_id = request.form.get('github_client_id')
        github_client_secret = request.form.get('github_client_secret')
        if github_client_id and github_client_secret:
            user.github_client_id = github_client_id
            user.github_client_secret = github_client_secret
            db.session.commit()
            return redirect(url_for('github_login'))
    return render_template('link_github.html')


@app.route('/github-login')
def github_login():
    """
    Redirects the user to GitHub's OAuth login page if client_id and client_secret are stored.
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))

    if user.github_client_id and user.github_client_secret:
        # Set GitHub OAuth credentials dynamically for the user
        github.client_id = user.github_client_id
        github.client_secret = user.github_client_secret

        # Redirect to GitHub's OAuth login page
        return github.authorize_redirect(
            url_for('github_callback', _external=True),
            prompt='consent'  # Always prompt the user for GitHub authentication
        )

    # Redirect to link_github.html if credentials are missing
    return redirect(url_for('link_github'))



@app.route('/github-callback')
def github_callback():
    """
    Handles the OAuth callback and saves the GitHub token in the database.
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))

    # Get the OAuth token from GitHub
    token = github.authorize_access_token()
    if not token:
        return redirect(url_for('index'))

    # Save the OAuth token in the user's database record
    user.github_token = token['access_token']
    db.session.commit()

    # Redirect to the GitHub assignments page
    return redirect(url_for('github_assignments'))



@app.route('/github-assignments')
def github_assignments():
    """
    Fetches and categorizes the user's GitHub repositories into:
    - Assignments with deadlines: Repositories with a Classroom button link in the README.
    - Other projects: Repositories without a Classroom button link.
    """
    user = current_user()
    if not user or not user.github_token:
        return redirect(url_for('github_login'))

    github.token = {'access_token': user.github_token}

    # Fetch the user's repositories
    repos = github.get('/user/repos').json()

    # Categorize repositories
    assignments_with_deadlines = []
    other_projects = []

    for repo in repos:
        repo_name = repo['name']
        owner = repo['owner']['login']

        # Fetch the README file
        try:
            readme_response = github.get(f'/repos/{owner}/{repo_name}/contents/README.md')
            if readme_response.status_code == 200:
                # Decode the README content (Base64)
                readme_content = readme_response.json().get('content', '')
                readme_decoded = base64.b64decode(readme_content).decode('utf-8')

                # Look for the Classroom button link
                button_link_match = re.search(
                    r'\[!\[Review Assignment Due Date\]\(https://classroom\.github\.com/assets/.*?\.svg\)\]\((https://classroom\.github\.com/a/[a-zA-Z0-9]+)\)',
                    readme_decoded
                )

                if button_link_match:
                    # Found the Classroom button link
                    assignment_url = button_link_match.group(1)

                    # Add repository to the assignments with deadlines
                    assignments_with_deadlines.append({
                        'name': repo_name,
                        'github_url': repo['html_url'],
                        'classroom_url': assignment_url
                    })
                else:
                    # No Classroom button link found
                    other_projects.append({'name': repo_name, 'url': repo['html_url']})
            else:
                # README could not be fetched
                other_projects.append({'name': repo_name, 'url': repo['html_url']})
        except Exception as e:
            # Handle any unexpected errors when processing the repository
            other_projects.append({'name': repo_name, 'url': repo['html_url'], 'error': str(e)})

    return render_template(
        'github_assignments.html',
        assignments_with_deadlines=assignments_with_deadlines,
        other_projects=other_projects
    )


if __name__ == '__main__':
    app.run(debug=True)
