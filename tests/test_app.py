import pytest
from app.server import app, db, User, Task


@pytest.fixture
def client():
    """Set up a Flask test client and test database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory DB
    app.config["SECRET_KEY"] = "test_secret"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


# --------------- Authentication Tests ---------------

def test_register(client):
    """Test user registration."""
    response = client.post("/signup", data={
        "username": "testuser",
        "password": "testpassword"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"This username is already taken" not in response.data  # Ensure successful registration


def test_register_existing_user(client):
    """Test registering with an existing username."""
    client.post("/signup", data={
        "username": "existinguser",
        "password": "password123"
    })

    response = client.post("/signup", data={
        "username": "existinguser",
        "password": "newpassword"
    })

    assert response.status_code == 400
    assert b"This username is already taken" in response.data


def test_login(client):
    """Test successful login."""
    client.post("/signup", data={
        "username": "loginuser",
        "password": "securepass"
    })

    response = client.post("/login", data={
        "username": "loginuser",
        "password": "securepass"
    }, follow_redirects=True)

    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess["user_id"] is not None  # Ensure user session is created


def test_login_invalid(client):
    """Test login with wrong credentials."""
    response = client.post("/login", data={
        "username": "wronguser",
        "password": "wrongpassword"
    })

    assert response.status_code == 400
    assert b"Invalid username or password" in response.data


def test_logout(client):
    """Test user logout."""
    client.post("/signup", data={
        "username": "logoutuser",
        "password": "password"
    })
    client.post("/login", data={
        "username": "logoutuser",
        "password": "password"
    })

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert "user_id" not in sess  # Ensure session is cleared


# --------------- Task Management Tests ---------------

def test_add_task(client):
    """Test adding a task to a specific date."""
    client.post("/signup", data={
        "username": "taskuser",
        "password": "taskpassword"
    })
    client.post("/login", data={
        "username": "taskuser",
        "password": "taskpassword"
    })

    response = client.post("/tasks/2024/02/01", data={
        "task": "Complete assignment"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Complete assignment" in response.data  # Check if task appears


def test_fetch_tasks(client):
    """Test fetching tasks for a specific date."""
    client.post("/signup", data={
        "username": "fetchuser",
        "password": "fetchpassword"
    })
    client.post("/login", data={
        "username": "fetchuser",
        "password": "fetchpassword"
    })

    client.post("/tasks/2024/02/01", data={"task": "Complete project"})

    response = client.get("/tasks/2024/02/01")
    assert response.status_code == 200
    assert b"Complete project" in response.data  # Ensure task is listed


def test_mark_task_done(client):
    """Test marking a task as done."""
    client.post("/signup", data={
        "username": "doneuser",
        "password": "donepassword"
    })
    client.post("/login", data={
        "username": "doneuser",
        "password": "donepassword"
    })

    # Add task
    client.post("/tasks/2024/02/01", data={"task": "Finish report"})

    # Retrieve task ID
    with app.app_context():
        task = Task.query.filter_by(user_id=1, task_text="Finish report").first()
        assert task is not None

    # Mark task as done
    response = client.post("/mark_finished", data={"task_id": task.id}, follow_redirects=True)
    assert response.status_code == 200

    # Verify task status update
    with app.app_context():
        updated_task = Task.query.get(task.id)
        assert updated_task.status == "Done"


# --------------- Authorization Tests ---------------

def test_unauthorized_task_access(client):
    """Ensure unauthorized users cannot access task pages."""
    response = client.get("/tasks/2024/02/01")
    assert response.status_code == 302  # Redirect to login page


def test_unauthorized_mark_task_done(client):
    """Ensure unauthorized users cannot mark a task as done."""
    response = client.post("/mark_finished", data={"task_id": 1})
    assert response.status_code == 302  # Redirect to login page
