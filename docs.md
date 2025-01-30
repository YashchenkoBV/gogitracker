# GoGiTracker Documentation

## **Authentication**
### `GET /signup`
- **Displays**: Registration form.
- **Purpose**: Register a new user.
- **Elements**:
  - Input fields: `username`, `password`
  - Submit button.
- **Responses**:
  - `200` → Successfully renders the signup page.
  - `302` → Redirects to the login page after successful signup.
  - `400` → Invalid input (username taken, weak password, or other errors).
  - `500` → Server error while creating the user.

---

### `POST /signup`
- **Processes**: User registration.
- **Action**: Creates a new user in the database.
- **Responses**:
  - `302` → Redirects to login after successful signup.
  - `400` → Invalid username or password format.
  - `500` → Internal error during user creation.

---

### `GET /login`
- **Displays**: Login form.
- **Purpose**: Authenticate and log in a user.
- **Elements**:
  - Input fields: `username`, `password`
  - Submit button.
- **Responses**:
  - `200` → Successfully renders the login page.
  - `400` → Invalid credentials.

---

### `POST /login`
- **Processes**: User login.
- **Action**: Verifies user credentials and starts a session.
- **Responses**:
  - `302` → Redirects to the main page after successful login.
  - `400` → Invalid credentials.

---

### `GET /logout`
- **Action**: Logs the user out and clears the session.
- **Redirects**: To the home page (`/`).
- **Responses**:
  - `200` → Successfully logged out.

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
- **Responses**:
  - `200` → Successfully rendered the main page.
  - `302` → Redirects to the welcome page if not logged in.

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
- **Responses**:
  - `200` → Successfully renders the task page.
  - `302` → Redirects to login if not authenticated.

---

### `POST /tasks/<year>/<month>/<day>`
- **Processes**:
  - Adds a **new task**.
  - Marks an **existing task as completed**.
- **Responses**:
  - `302` → Redirects after adding or updating a task.
  - `400` → Invalid request (e.g., missing task data).
  - `500` → Internal server error while processing the request.

---

### `POST /mark_finished`
- **Action**: Marks a task as **"Done"**.
- **Redirects**: Back to the main page.
- **Responses**:
  - `302` → Successfully marked as done.

---

## **GitHub Integration**
### `GET /link-github`
- **Displays**: A form where users **input their GitHub OAuth Client ID & Secret**.
- **Purpose**: Set up GitHub authentication credentials.
- **Responses**:
  - `200` → Successfully renders the GitHub linking page.
  - `302` → Redirects to GitHub login after successful credential update.
  - `400` → Invalid request (e.g., missing credentials).
  - `401` → Unauthorized access (user not logged in).
  - `500` → Internal server error while updating credentials.

---

### `POST /link-github`
- **Processes**:
  - Stores the **GitHub Client ID & Secret** in the user's profile.
  - Redirects the user to **GitHub OAuth login**.
- **Responses**:
  - `302` → Redirects to GitHub login.
  - `400` → Missing credentials.
  - `500` → Internal server error.

---

### `GET /github-login`
- **Redirects**:
  - If **GitHub credentials are stored** → Directly sends the user to **GitHub OAuth login**.
  - If **GitHub credentials are missing** → Redirects to `/link-github` to collect them.
- **Triggers GitHub Authentication** using `prompt=consent` to always require re-authentication.
- **Responses**:
  - `302` → Redirects to GitHub OAuth login.
  - `401` → Unauthorized access.
  - `400` → GitHub credentials missing.

---

### `GET /github-callback`
- **Processes GitHub OAuth Response**:
  - Stores the **GitHub Access Token**.
  - Redirects the user to `/github-assignments`.
- **Responses**:
  - `302` → Redirects to GitHub assignments page after successful authentication.
  - `401` → Unauthorized access.
  - `400` → Failed to retrieve OAuth token from GitHub.
  - `500` → Internal server error while saving GitHub token.

---

### `GET /github-assignments`
- **Displays**: **Two columns** of repositories:
  1. **Assignments with deadlines** (includes **"Review Deadline"** link).
  2. **Other projects**.
- **Uses GitHub API** to:
  - Fetch the user's **repositories**.
  - Identify repositories that have **GitHub Classroom assignment deadlines**.
- **Responses**:
  - `200` → Successfully fetched and categorized repositories.
  - `302` → Redirects to GitHub login if user is not authenticated.
  - `400` → Failed to fetch GitHub repositories.
  - `500` → Internal server error while processing repositories.

---

