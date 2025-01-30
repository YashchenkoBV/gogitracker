from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import calendar
from datetime import datetime, date
from authlib.integrations.flask_client import OAuth
import base64
import re
import logging
from flasgger import Swagger


# Singleton Logger Class
class SingletonLogger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SingletonLogger, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("GoGiTracker")
            cls._instance.logger.setLevel(logging.DEBUG)  # Set the base logging level

            # Create a file handler
            file_handler = logging.FileHandler("../gogitracker.log")
            file_handler.setLevel(logging.DEBUG)

            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Create a logging format
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            cls._instance.logger.addHandler(file_handler)
            cls._instance.logger.addHandler(console_handler)
        return cls._instance

    def get_logger(self):
        return self.logger


# Initialize the Singleton Logger
logger = SingletonLogger().get_logger()

app = Flask(__name__, template_folder="../templates")
Swagger(app)
app.config.from_pyfile('../keys/config.py')
app.secret_key = app.config['SECRET_KEY']

# Configure SQLAlchemy (using SQLite for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../users.db'
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
    try:
        db.create_all()
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


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


from flask import jsonify

@app.route('/')
def index():
    """
    Main index page that displays tasks and calendar for the logged-in user.

    ---
    tags:
      - Pages
    parameters:
      - name: year
        in: query
        type: integer
        required: false
        default: Current Year
        description: The year to display tasks for.
      - name: month
        in: query
        type: integer
        required: false
        default: Current Month
        description: The month to display tasks for.
      - name: show_done
        in: query
        type: boolean
        required: false
        default: false
        description: Whether to show completed tasks.
    responses:
      200:
        description: Successfully rendered the index page.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirect to welcome page if user is not logged in.
    """
    if not current_user():
        logger.info("User not logged in. Redirecting to welcome page.")
        return render_template("welcome.html"), 302

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

    # Ensure upcoming tasks are always shown, even when viewing done tasks
    upcoming_tasks = (
        Task.query
        .filter(Task.user_id == user.id, Task.date >= now.date(), Task.status == "In Progress")
        .order_by(Task.date)
        .limit(10)
        .all()
    )

    for task in upcoming_tasks:
        task.days_left = (task.date - now.date()).days + 1

    logger.info(f"Rendering index page for user: {user.username}")
    return render_template(
        "index.html",
        current_user=user,
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days,
        tasks_by_date=tasks_by_date,  # Ensures done tasks appear for past dates
        upcoming_tasks=upcoming_tasks,
        is_past=is_past,
        now=now,
        show_done_tasks=show_done_tasks
    ), 200





@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User signup page.

    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              username:
                type: string
                example: "newuser"
                description: The desired username.
              password:
                type: string
                format: password
                example: "securepassword123"
                description: The password for the new account (minimum 8 characters).
    responses:
      200:
        description: Successfully renders the signup page.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirects to the login page after successful signup.
      400:
        description: Invalid input (username taken, weak password, or other errors).
        content:
          text/html:
            example: "<html><body>Error: Username already taken</body></html>"
      500:
        description: Server error while creating the user.
        content:
          text/html:
            example: "<html><body>Error: An error occurred while creating the user.</body></html>"
    """

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            logger.warning("Signup attempt with missing fields.")
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="Both username and password are required."
            ), 400

        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            logger.warning(f"Username '{username}' is already taken.")
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="This username is already taken."
            ), 400

        # Validate password
        if len(password) < 8:
            logger.warning("Password is too short.")
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="Password must be at least 8 characters long."
            ), 400

        # Hash the password and create a new user
        try:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"New user created: {username}")
            return redirect(url_for('login')), 302
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return render_template(
                'signup.html',
                current_user=current_user(),
                error_message="An error occurred while creating the user."
            ), 500

    logger.info("Rendering signup page.")
    return render_template('signup.html', current_user=current_user()), 200




@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.

    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              username:
                type: string
                example: "testuser"
                description: The username of the user.
              password:
                type: string
                format: password
                example: "securepassword123"
                description: The password of the user.
    responses:
      200:
        description: Successfully renders the login page.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirects to the index page after successful login.
      400:
        description: Invalid input (missing fields or incorrect credentials).
        content:
          text/html:
            example: "<html><body>Error: Invalid username or password</body></html>"
    """

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            logger.warning("Login attempt with missing fields.")
            return render_template(
                'login.html',
                current_user=current_user(),
                error_message="Both username and password are required."
            ), 400

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template(
                'login.html',
                current_user=current_user(),
                error_message="Invalid username or password."
            ), 400

        # Log in the user
        session['user_id'] = user.id
        logger.info(f"User logged in: {username}")
        return redirect(url_for('index')), 302

    logger.info("Rendering login page.")
    return render_template('login.html', current_user=current_user()), 200



@app.route('/logout')
def logout():
    """
    Log out the current user by clearing the session.
    """
    user = current_user()
    if user:
        logger.info(f"User logged out: {user.username}")
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
def tasks(year, month, day):
    """
    Manage tasks for a specific date.

    ---
    tags:
      - Tasks
    parameters:
      - name: year
        in: path
        type: integer
        required: true
        description: The year of the tasks.
      - name: month
        in: path
        type: integer
        required: true
        description: The month of the tasks.
      - name: day
        in: path
        type: integer
        required: true
        description: The day of the tasks.
    requestBody:
      required: false
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              task:
                type: string
                example: "Complete project report"
                description: The task to add (optional, only for POST).
              task_id:
                type: integer
                example: 1
                description: The ID of the task to mark as done (optional, only for POST).
    responses:
      200:
        description: Successfully renders the task page.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirects after adding or updating a task.
      400:
        description: Invalid request (e.g., unauthorized access, missing task data).
        content:
          text/html:
            example: "<html><body>Error: Invalid request</body></html>"
      500:
        description: Internal server error while processing the request.
        content:
          text/html:
            example: "<html><body>Error: An error occurred</body></html>"
    """

    if not current_user():
        logger.warning("Unauthorized access to tasks page. Redirecting to login.")
        return redirect(url_for('login')), 302

    user = current_user()
    date = datetime(year, month, day).date()

    if request.method == 'POST':
        if 'task' in request.form:  # Add a new task
            task_text = request.form.get('task')
            if not task_text:
                logger.warning("Attempt to add a task without text.")
                return render_template(
                    'tasks.html',
                    year=year,
                    month=month,
                    day=day,
                    tasks_in_progress=[],
                    done_tasks=[],
                    error_message="Task text cannot be empty."
                ), 400
            try:
                new_task = Task(user_id=user.id, date=date, task_text=task_text)
                db.session.add(new_task)
                db.session.commit()
                logger.info(f"New task added by user {user.username}: {task_text}")
                return redirect(url_for('tasks', year=year, month=month, day=day)), 302
            except Exception as e:
                logger.error(f"Error adding task: {e}")
                return render_template(
                    'tasks.html',
                    year=year,
                    month=month,
                    day=day,
                    tasks_in_progress=[],
                    done_tasks=[],
                    error_message="An error occurred while adding the task."
                ), 500

        elif 'task_id' in request.form:  # Update task status to "Done"
            task_id = request.form.get('task_id')
            task = Task.query.filter_by(id=task_id, user_id=user.id).first()
            if not task:
                logger.warning(f"Task ID {task_id} not found for user {user.username}.")
                return render_template(
                    'tasks.html',
                    year=year,
                    month=month,
                    day=day,
                    tasks_in_progress=[],
                    done_tasks=[],
                    error_message="Task not found."
                ), 400
            try:
                task.status = "Done"
                db.session.commit()
                logger.info(f"Task marked as done by user {user.username}: {task.task_text}")
                return redirect(url_for('tasks', year=year, month=month, day=day)), 302
            except Exception as e:
                logger.error(f"Error updating task status: {e}")
                return render_template(
                    'tasks.html',
                    year=year,
                    month=month,
                    day=day,
                    tasks_in_progress=[],
                    done_tasks=[],
                    error_message="An error occurred while updating the task."
                ), 500

    # Retrieve tasks categorized by status
    try:
        tasks_in_progress = Task.query.filter_by(user_id=user.id, date=date, status="In Progress").all()
        done_tasks = Task.query.filter_by(user_id=user.id, date=date, status="Done").all()
    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        return render_template(
            'tasks.html',
            year=year,
            month=month,
            day=day,
            tasks_in_progress=[],
            done_tasks=[],
            error_message="An error occurred while retrieving tasks."
        ), 500

    logger.info(f"Rendering tasks page for user {user.username} on {date}.")
    return render_template(
        'tasks.html',
        year=year,
        month=month,
        day=day,
        tasks_in_progress=tasks_in_progress,
        done_tasks=done_tasks
    ), 200



@app.route('/mark_finished', methods=['POST'])
def mark_finished():
    task_id = request.form.get('task_id')
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    show_done_tasks = request.args.get("show_done", "false").lower() == "true"

    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        try:
            task.status = "Done"
            db.session.commit()
            logger.info(f"Task marked as finished by user {current_user().username}: {task.task_text}")
        except Exception as e:
            logger.error(f"Error marking task as finished: {e}")

    return redirect(url_for('index', year=year, month=month, show_done=show_done_tasks))


@app.route('/link-github', methods=['GET', 'POST'])
def link_github():
    """
    Link GitHub OAuth credentials to the user account.

    ---
    tags:
      - GitHub Integration
    requestBody:
      required: false
      content:
        application/x-www-form-urlencoded:
          schema:
            type: object
            properties:
              github_client_id:
                type: string
                example: "your_github_client_id"
                description: The GitHub OAuth client ID.
              github_client_secret:
                type: string
                format: password
                example: "your_github_client_secret"
                description: The GitHub OAuth client secret.
    responses:
      200:
        description: Successfully renders the GitHub linking page.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirects to GitHub login after successful credential update.
      400:
        description: Invalid request (e.g., missing credentials).
        content:
          text/html:
            example: "<html><body>Error: Missing GitHub credentials</body></html>"
      401:
        description: Unauthorized access (user not logged in).
        content:
          text/html:
            example: "<html><body>Error: Unauthorized access</body></html>"
      500:
        description: Internal server error while updating credentials.
        content:
          text/html:
            example: "<html><body>Error: An error occurred</body></html>"
    """

    user = current_user()
    if not user:
        logger.warning("Unauthorized access to link-github page. Redirecting to login.")
        return redirect(url_for('login')), 401

    if request.method == 'POST':
        github_client_id = request.form.get('github_client_id')
        github_client_secret = request.form.get('github_client_secret')

        if not github_client_id or not github_client_secret:
            logger.warning("Missing GitHub credentials in link request.")
            return render_template(
                'link_github.html',
                error_message="GitHub client ID and secret are required."
            ), 400

        try:
            user.github_client_id = github_client_id
            user.github_client_secret = github_client_secret
            db.session.commit()
            logger.info(f"GitHub credentials updated for user {user.username}.")
            return redirect(url_for('github_login')), 302
        except Exception as e:
            logger.error(f"Error updating GitHub credentials: {e}")
            return render_template(
                'link_github.html',
                error_message="An error occurred while updating your GitHub credentials."
            ), 500

    logger.info("Rendering link-github page.")
    return render_template('link_github.html'), 200



@app.route('/github-login')
def github_login():
    """
    Redirects the user to GitHub's OAuth login page.

    ---
    tags:
      - GitHub Integration
    responses:
      302:
        description: Redirects to GitHub OAuth login if credentials are set.
      401:
        description: Unauthorized access (user not logged in).
        content:
          text/html:
            example: "<html><body>Error: Unauthorized access</body></html>"
      400:
        description: GitHub credentials missing.
        content:
          text/html:
            example: "<html><body>Error: GitHub credentials not found</body></html>"
    """

    user = current_user()
    if not user:
        logger.warning("Unauthorized access to github-login page. Redirecting to login.")
        return redirect(url_for('login')), 401

    if user.github_client_id and user.github_client_secret:
        try:
            # Set GitHub OAuth credentials dynamically for the user
            github.client_id = user.github_client_id
            github.client_secret = user.github_client_secret

            # Redirect to GitHub's OAuth login page
            logger.info(f"Redirecting user {user.username} to GitHub OAuth login.")
            return github.authorize_redirect(
                url_for('github_callback', _external=True),
                prompt='consent'  # Always prompt the user for GitHub authentication
            ), 302
        except Exception as e:
            logger.error(f"Error initiating GitHub OAuth redirect: {e}")
            return redirect(url_for('link_github')), 400

    # Redirect to link_github.html if credentials are missing
    logger.warning("GitHub credentials missing. Redirecting to link-github page.")
    return redirect(url_for('link_github')), 400


@app.route('/github-callback')
def github_callback():
    """
    Handles the GitHub OAuth callback and saves the GitHub token in the database.

    ---
    tags:
      - GitHub Integration
    responses:
      302:
        description: Redirects to GitHub assignments page after successful authentication.
      401:
        description: Unauthorized access (user not logged in).
        content:
          text/html:
            example: "<html><body>Error: Unauthorized access</body></html>"
      400:
        description: Failed to retrieve OAuth token from GitHub.
        content:
          text/html:
            example: "<html><body>Error: OAuth token not received</body></html>"
      500:
        description: Internal server error while saving GitHub token.
        content:
          text/html:
            example: "<html><body>Error: Could not save GitHub token</body></html>"
    """

    user = current_user()
    if not user:
        logger.warning("Unauthorized access to github-callback page. Redirecting to login.")
        return redirect(url_for('login')), 401

    try:
        # Get the OAuth token from GitHub
        token = github.authorize_access_token()
        if not token or 'access_token' not in token:
            logger.error("Failed to retrieve OAuth token from GitHub.")
            return redirect(url_for('index')), 400

        # Save the OAuth token in the user's database record
        user.github_token = token['access_token']
        db.session.commit()
        logger.info(f"GitHub token saved for user {user.username}.")

        return redirect(url_for('github_assignments')), 302

    except Exception as e:
        logger.error(f"Error saving GitHub token: {e}")
        return redirect(url_for('index')), 500


@app.route('/github-assignments')
def github_assignments():
    """
    Fetches and categorizes the user's GitHub repositories.

    ---
    tags:
      - GitHub Integration
    responses:
      200:
        description: Successfully fetched and categorized repositories.
        content:
          text/html:
            example: "<html>...</html>"
      302:
        description: Redirects to GitHub login if user is not authenticated.
      400:
        description: Failed to fetch GitHub repositories.
        content:
          text/html:
            example: "<html><body>Error: Failed to fetch repositories</body></html>"
      500:
        description: Internal server error while processing repositories.
        content:
          text/html:
            example: "<html><body>Error: Server error occurred</body></html>"
    """

    user = current_user()
    if not user or not user.github_token:
        logger.warning("Unauthorized access to github-assignments page. Redirecting to github-login.")
        return redirect(url_for('github_login')), 302

    try:
        github.token = {'access_token': user.github_token}

        # Fetch the user's repositories
        repos_response = github.get('/user/repos')
        if repos_response.status_code != 200:
            logger.error(f"Failed to fetch GitHub repositories: {repos_response.text}")
            return render_template('error.html', error_message="Failed to fetch GitHub repositories."), 400

        repos = repos_response.json()
        logger.info(f"Fetched GitHub repositories for user {user.username}.")
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories: {e}")
        return render_template('error.html', error_message="An error occurred while fetching repositories."), 500

    # Categorize repositories
    assignments_with_deadlines = []
    other_projects = []

    for repo in repos:
        repo_name = repo.get('name', 'Unknown')
        owner = repo.get('owner', {}).get('login', 'Unknown')
        repo_url = repo.get('html_url', '#')

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

                    assignments_with_deadlines.append({
                        'name': repo_name,
                        'github_url': repo_url,
                        'classroom_url': assignment_url
                    })
                    logger.debug(f"Repository '{repo_name}' has a Classroom deadline link.")
                else:
                    other_projects.append({'name': repo_name, 'url': repo_url})
                    logger.debug(f"Repository '{repo_name}' has no Classroom deadline link.")
            else:
                other_projects.append({'name': repo_name, 'url': repo_url})
                logger.debug(f"Repository '{repo_name}' has no README or no Classroom deadline link.")

        except Exception as e:
            other_projects.append({'name': repo_name, 'url': repo_url, 'error': str(e)})
            logger.error(f"Error processing repository '{repo_name}': {e}")

    logger.info(f"Successfully categorized repositories for user {user.username}.")
    return render_template(
        'github_assignments.html',
        assignments_with_deadlines=assignments_with_deadlines,
        other_projects=other_projects
    ), 200


@app.route('/rep_date/<repo_name>', methods=['GET'])
def rep_date(repo_name):
    """
    Page to enter a date for adding a repository as a task.
    """
    return render_template('rep_date.html', repo_name=repo_name)


@app.route('/add_repo_task/<repo_name>', methods=['POST'])
def add_repo_task(repo_name):
    """
    Add a repository as a task to the calendar.
    """
    user = current_user()
    if not user:
        return redirect(url_for('login'))

    task_date_str = request.form.get('task_date')
    task_date = datetime.strptime(task_date_str, '%Y-%m-%d').date()

    # Add the repository as a task (only the repo name)
    new_task = Task(user_id=user.id, date=task_date, task_text=repo_name)
    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
