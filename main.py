from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="local host",
    user="root",
    password="root",
    database="angajati"
)

cursor = db.cursor()

@app.route('/')
def index():
    cursor.execute("SELECT * FROM angajati")
    angajati = cursor.fetchall()
    return render_template('index.html', angajati=angajati)

if __name__ == '__main__':
    app.run(debug=True)