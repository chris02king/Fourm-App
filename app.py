from flask import Flask, render_template, request, jsonify
import sqlite3
import time
import psutil

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            good_host TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comments TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_feedback():
    data = request.get_json()

    name = data.get('name')
    good_host = data.get('good_host')
    visit_date = data.get('visit_date')
    rating = data.get('rating')
    comments = data.get('comments')

    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedback (name, good_host, visit_date, rating, comments)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, good_host, visit_date, rating, comments))
    conn.commit()
    conn.close()

    return jsonify({"message": "Feedback submitted successfully!"}), 200

@app.route('/feedback')
def view_feedback():
    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, good_host, visit_date, rating, comments FROM feedback")
    rows = cursor.fetchall()
    conn.close()
    return render_template('feedback.html', rows=rows)


@app.route('/manage', methods=['GET', 'POST'])
def manage_db():
    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Deleting a row
        feedback_id = request.form.get('id')
        cursor.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
        conn.commit()

    # Retrieve all rows from the feedback table
    cursor.execute('SELECT id, name, good_host, visit_date, rating, comments FROM feedback')
    rows = cursor.fetchall()
    conn.close()

    return render_template('manage.html', rows=rows)

import time
import os
import sqlite3
import psutil
from flask import jsonify

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    # Start timing
    start_time = time.time()

    # Check if database is available
    try:
        conn = sqlite3.connect('trip_feedback.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = "Database is available"
    except Exception as e:
        db_status = f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()

    # Measure page load time
    page_load_time = time.time() - start_time

    # Get container/system metrics (using psutil)
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)

    health_metrics = {
        "db_status": db_status,
        "page_load_time": f"{page_load_time:.4f} seconds",
        "memory_usage": f"{memory_usage}%",
        "cpu_usage": f"{cpu_usage}%",
    }

    return jsonify(health_metrics), 200




if __name__ == '__main__':
    app.run(debug=True)