# GoGiTracker API Documentation

## **Authentication**
### `GET /signup`
- **Displays**: Registration form.
- **Purpose**: Register a new user.
- **Elements**:
  - Input fields: `username`, `password`
  - Submit button.

### `POST /signup`
- **Processes**: User registration.
- **Action**: Creates a new user in the database.

---

### `GET /login`
- **Displays**: Login form.
- **Purpose**: Authenticate and log in a user.
- **Elements**:
  - Input fields: `username`, `password`
  - Submit button.

### `POST /login`
- **Processes**: User login.
- **Action**: Verifies user credentials and starts a session.

---

### `GET /logout`
- **Action**: Logs the user out and clears the session.
- **Redirects**: To the home page (`/`).

---

## **Task & Calendar Management**
### `GET /`
- **Displays**: User's **calendar** and upcoming **tasks**.
- **Features**:
  - View **tasks** sorted by date.
  - Navigate **calendar months**.
  - Toggle between **completed & pending tasks**.
- **Query Parameters**:
  - `year` (optional, integer) → Default: Current Year.
  - `month` (optional, integer) → Default: Current Month.
  - `show_done` (optional, boolean) → Default: `false` (shows only "In Progress" tasks).

---

### `GET /tasks/<year>/<month>/<day>`
- **Displays**: Tasks for a specific date.
- **Actions**:
  - View **tasks**.
  - **Add new tasks**.
  - **Mark tasks as completed**.
- **Elements**:
  - Task list (separated into **"In Progress"** and **"Done"**).
  - Input form to add a task.

---

### `POST /tasks/<year>/<month>/<day>`
- **Processes**:
  - Adds a **new task**.
  - Marks an **existing task as completed**.

---

### `POST /mark_finished`
- **Action**: Marks a task as **"Done"**.
- **Redirects**: Back to the main page.

---

## **GitHub Integration**
### `GET /link-github`
- **Displays**: A form where users **input their GitHub OAuth Client ID & Secret**.
- **Purpose**: Set up GitHub authentication credentials.

---

### `POST /link-github`
- **Processes**:
  - Stores the **GitHub Client ID & Secret** in the user's profile.
  - Redirects the user to **GitHub OAuth login**.

---

### `GET /github-login`
- **Redirects**:
  - If **GitHub credentials are stored** → Directly sends the user to **GitHub OAuth login**.
  - If **GitHub credentials are missing** → Redirects to `/link-github` to collect them.
- **Triggers GitHub Authentication** using `prompt=consent` to always require re-authentication.

---

### `GET /github-callback`
- **Processes GitHub OAuth Response**:
  - Stores the **GitHub Access Token**.
  - Redirects the user to `/github-assignments`.

---

### `GET /github-assignments`
- **Displays**: **Two columns** of repositories:
  1. **Assignments with deadlines** (includes **"Review Deadline"** link).
  2. **Other projects**.
- **Uses GitHub API** to:
  - Fetch the user's **repositories**.
  - Identify repositories that have **GitHub Classroom assignment deadlines**.

---

### `GET /rep_date/<repo_name>`
- **Displays**: A form to **schedule** a repository as a task.
- **Elements**:
  - Input field: **Task due date**.
  - Submit button.

---

### `POST /add_repo_task/<repo_name>`
- **Processes**:
  - Converts a **GitHub repository** into a **calendar task**.
  - Saves the repository name as a task in the database.
- **Redirects**: Back to `/`.

---
 
