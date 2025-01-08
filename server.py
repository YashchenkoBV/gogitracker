from flask import Flask, request, render_template, redirect, url_for, session, jsonify

app = Flask(__name__, template_folder='templates')

# In-memory storage for demonstration purposes
users = {}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        # Render the signup template
        return render_template('signup.html')
    elif request.method == 'POST':
        # Handle form submission
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users:
            return jsonify({'error': 'User already exists!'}), 400
        else:
            users[username] = password
            return jsonify({'message': 'User created successfully!'})

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        # Render the signin template
        return render_template('signin.html')
    elif request.method == 'POST':
        # Handle form submission
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['username'] = username
            return jsonify({'message': f'Welcome, {username}!'})
        else:
            return jsonify({'error': 'Invalid username or password!'}), 401

if __name__ == '__main__':
    app.run(debug=True)
