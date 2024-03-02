from flask import Flask, render_template, request
import mysql.connector
from flask import jsonify

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="angajati"
)

cursor = db.cursor()

@app.route('/')
def index():
    cursor.execute("SELECT id, nume, prenume, id_manager, companie FROM angajati")
    users = cursor.fetchall()
    print(users)
    return render_template('index.html', users=users)

@app.route('/user', methods=['POST'])
def add_user():
    # Luam datele din request
    data = request.get_json()
    nume = data.get('nume')
    prenume = data.get('prenume')
    id_manager = data.get('id_manager')
    companie = data.get('companie')
    
    cursor = db.cursor()
    response = {}
    
    try:
        # Inseram noul user in tabela
        cursor.execute("INSERT INTO angajati (nume, prenume, id_manager, companie) VALUES (%s, %s, %s, %s)", 
                       (nume, prenume, id_manager, companie))
        db.commit()
        response["status"] = "success"
        response["message"] = "User added successfully."
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        response["status"] = "error"
        response["message"] = "Failed to add user."
    finally:
        cursor.close()
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)