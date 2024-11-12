from flask import Flask, jsonify
import json

app = Flask(__name__)

# Helper function to load tasks from JSON file
def load_tasks():
    with open('tasks.json') as file:
        return json.load(file)


# Route to get the deadline by task title
@app.route('/deadline/<title>', methods=['GET'])
def get_deadline_by_title(title):
    tasks = load_tasks()
    # Search for the task with the specified title
    for task in tasks:
        if task['title'].lower() == title.lower():
            return jsonify({"title": task['title'], "deadline": task['deadline']})
    # If task not found, return a 404 error
    return jsonify({"error": "Task not found"}), 404
@app.route('/')
def home():
    return 'Task tracker'