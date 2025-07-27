from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import re
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

client = MongoClient("mongodb://localhost:27017/")
db = client['taskmanager']
users = db['users']
tasks = db['tasks']

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    user_tasks = tasks.find({'user_id': session['user_id']})
    return render_template('index.html', tasks=user_tasks)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email"
        if len(password) < 6:
            return "Password must be at least 6 characters"
        if users.find_one({'username': username}):
            return "Username already exists"

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        users.insert_one({
            'email': email,
            'username': username,
            'password': hashed,
            'role': 'user'
        })
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user.get('role', 'user')
            return redirect('/admin' if session['role'] == 'admin' else '/')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')
    all_users = users.find()
    return render_template('admin.html', users=all_users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tasks.insert_one({
            'title': title,
            'description': description,
            'user_id': session['user_id']
        })
        return redirect('/')
    return render_template('add.html')

@app.route('/edit/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = tasks.find_one({'_id': ObjectId(task_id)})
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {
            'title': title,
            'description': description
        }})
        return redirect('/')
    return render_template('edit.html', task=task)

@app.route('/delete/<task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect('/login')
    tasks.delete_one({'_id': ObjectId(task_id), 'user_id': session['user_id']})
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
