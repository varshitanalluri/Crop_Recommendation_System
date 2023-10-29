from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
import pickle

from joblib import load

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the Random Forest model
with open('model.pkl', 'rb') as file:
    model = pickle.load(file)

# Connect to SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

# Create recommendation_inputs table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendation_inputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        nitrogen INTEGER NOT NULL,
        phosphorus INTEGER NOT NULL,
        potassium INTEGER NOT NULL,
        temperature INTEGER NOT NULL,
        humidity INTEGER NOT NULL,
        ph_value INTEGER NOT NULL,
        rainfall INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')

conn.close()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, username, password) VALUES (?, ?, ?, ?)',
                       (name, email, username, password))
        conn.commit()
        conn.close()

        return render_template('register.html', registration_successful=True)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[3]  # Store username in session
            return redirect(url_for('recommend'))
        else:
            return render_template('login.html', login_error=True)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nitrogen = int(request.form['Nitrogen'])
        phosphorus = int(request.form['Phosphorus'])
        potassium = int(request.form['Potassium'])
        temperature = int(request.form['Temperature'])
        humidity = int(request.form['Humidity'])
        ph_value = int(request.form['pH Value'])
        rainfall = int(request.form['Rainfall'])
        username = session['username']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Clear old input values for the user
        cursor.execute('DELETE FROM recommendation_inputs WHERE user_id = ?', (username,))

        # Insert new input values
        cursor.execute(
            'INSERT INTO recommendation_inputs (user_id, nitrogen, phosphorus, potassium, temperature, humidity, '
            'ph_value, rainfall) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (username, nitrogen, phosphorus, potassium, temperature, humidity, ph_value, rainfall)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('result'))

    return render_template('recommend.html')



@app.route('/result')
def result():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recommendation_inputs WHERE user_id = ?', (session['username'],))
    inputs = cursor.fetchone()
    conn.close()

    if inputs:
        nitrogen, phosphorus, potassium, temperature, humidity, ph_value, rainfall = inputs[2:]

        input_data = pd.DataFrame({
            'Nitrogen': [nitrogen],
            'Phosphorus': [phosphorus],
            'Potassium': [potassium],
            'Temperature': [temperature],
            'Humidity': [humidity],
            'pH Value': [ph_value],
            'Rainfall': [rainfall]
        })

        print("Input data:\n", input_data)

        crop_label = model.predict(input_data)[0]

        print("Output data:", crop_label)

        return render_template('result.html', crop_name=crop_label)
    else:
        return redirect(url_for('recommend'))


if __name__ == '__main__':
    app.run()