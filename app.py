from flask import Flask, render_template, request, jsonify
import sqlite3

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

if __name__ == '__main__':
    app.run(debug=True)