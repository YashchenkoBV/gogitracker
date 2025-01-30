[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/d2zEkl7e)

# CS_2024_project

# GoGiTracker

## Description

A flask-based task-tracker, which provides tools for effective task management with calendar-like interface. This app
supports linking GitHub as an external platform to add tasks from there directly to the calendar.

## Video
By the link below, please find the demostration of how the applictaion works:
```
https://youtu.be/AduSZlzVGfA
```

## Setup

### 1. Access remote deployment via the link below:

```
flask-project-yashchenkobv-production-0ec4.up.railway.app
```

### 2. Running on local machine

1) Clone the repository

```bash
git clone https://github.com/nup-csai/flask-project-YashchenkoBV.git
cd flask-project-YashchenkoBV
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Run tests

```bash
$env:PYTHONPATH="." ; pytest tests/ --disable-warnings
```

4) Run the Flask application

```bash
flask --app app/server.py run
```

## Linking GitHub
To link GitHub to the web application, got to your GitHub profile > Setting > Developer Settings > OAuth apps and provide urls for homepage and authorization callback:
```
https://flask-project-yashchenkobv-production-0ec4.up.railway.app
https://flask-project-yashchenkobv-production-0ec4.up.railway.app/github-callback
```
Then enter Client ID and Client t Secret

## Requirements

- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Werkzeug
- Authlib
- pytest
- requests
- flasgger
- Docker

## Features

* User registration and authentication
* Linking assignments to particular dates and viewing them in the calendar grid
* Showing most urgent tasks ("Upcoming tasks" on the main page)
* Tasks can have different statuses ("In progress" or "Done")
* Ability lo link an external platfrom (namely, GitHub) and add assignments from there
* Storing data for different users

## Git

master branch

## Routes


#### **Authentication**
- **`GET /signup`** - Displays the **user registration page**.
- **`POST /signup`** - Handles **user registration**.
- **`GET /login`** - Displays the **user login page**.
- **`POST /login`** - Handles **user authentication**.
- **`GET /logout`** - Logs out the current user.

---

#### **Tasks & Calendar**
- **`GET /`** - Displays the **main page**, showing the **calendar and task list**.
- **`GET /tasks/<year>/<month>/<day>`** - Displays tasks for a **specific date**.
- **`POST /tasks/<year>/<month>/<day>`** - Adds a new task or **marks a task as completed**.
- **`POST /mark_finished`** - Marks a **task as "Done"**.

---

#### **GitHub Integration**
- **`GET /link-github`** - Displays a **form to input GitHub OAuth credentials**.
- **`POST /link-github`** - Saves **GitHub Client ID & Secret**.
- **`GET /github-login`** - Redirects to **GitHub OAuth login**.
- **`GET /github-callback`** - Handles the **GitHub OAuth callback** and saves the token.
- **`GET /github-assignments`** - Fetches and displays **GitHub repositories** (assignments with deadlines & other projects).

---

#### **GitHub Task Management**
- **`GET /rep_date/<repo_name>`** - Displays a form to **set a task date for a GitHub repo**.
- **`POST /add_repo_task/<repo_name>`** - Saves a **GitHub repo as a calendar task**.


## Success Criteria

* User is able to add tasks to the calendar, mark tasks done and view which tasks are in progress and which are finished
* Ability to link GitHub and add assignments from there
* Fine working registration and authorization

