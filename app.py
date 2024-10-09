from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import time
import psutil
import csv
from io import StringIO
from functools import wraps
import boto3
import base64
from botocore.exceptions import ClientError
import json

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

# AWS Secrets Manager Integration
def get_secret():
    secret_name = "fourm-app-secrets"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise Exception("Couldn't retrieve secret from AWS Secrets Manager.") from e

    # Decrypts secret using the associated KMS key
    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
    else:
        secret = base64.b64decode(get_secret_value_response["SecretBinary"])

    # Parse the secret and return it as a dictionary
    return json.loads(secret)

### 1. User Authentication ###
def check_auth(username, password):
    """This function is called to check if a username/password combination is valid."""
    secret = get_secret()  # Retrieve username and password from AWS Secrets Manager
    return username == secret["username"] and password == secret["password"]

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Login required.\n'
        'You have to login with the correct credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

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

### 2. Manage Database (protected by authentication) ###
@app.route('/manage', methods=['GET', 'POST'])
@requires_auth
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

### 3. Healthcheck ###
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

### 4. Export Feedback as CSV (protected by authentication) ###
@app.route('/export_csv', methods=['GET'])
@requires_auth
def export_csv():
    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, good_host, visit_date, rating, comments FROM feedback')
    rows = cursor.fetchall()
    conn.close()

    # Create CSV in-memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Good Host?', 'Visit Date', 'Rating', 'Comments'])
    writer.writerows(rows)

    output.seek(0)

    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=feedback.csv"})

### 5. Feedback Analytics Dashboard (protected by authentication) ###
@app.route('/analytics', methods=['GET'])
@requires_auth
def analytics():
    conn = sqlite3.connect('trip_feedback.db')
    cursor = conn.cursor()

    # Calculate the average rating
    cursor.execute('SELECT AVG(rating) FROM feedback')
    avg_rating = cursor.fetchone()[0] or 0

    # Count 'Good Host' responses
    cursor.execute('SELECT COUNT(*) FROM feedback WHERE good_host = "Yes"')
    good_host_count = cursor.fetchone()[0]

    # Total feedback submissions
    cursor.execute('SELECT COUNT(*) FROM feedback')
    total_feedback = cursor.fetchone()[0]

    conn.close()

    return render_template('analytics.html', avg_rating=avg_rating, good_host_count=good_host_count, total_feedback=total_feedback)


if __name__ == '__main__':
    app.run(debug=True)