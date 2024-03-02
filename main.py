from flask import Flask, render_template, request
import mysql.connector
from flask import jsonify
import os
import time
from threading import Thread
import pandas as pd
from shutil import move
from datetime import datetime, timedelta
from ProcesorFisierCsv import ProcesorFisierCsv
from ProcesorFisierTxt import ProcesorFisierTxt
from EmailSender import MailSender
from apscheduler.schedulers.background import BackgroundScheduler
import csv

aplicatie = Flask(__name__)

bd = mysql.connector.connect(
    host="localhost", user="root", password="root", database="angajati"
)

cursor = bd.cursor()

DOSAR_SUPRAVEGHERE = "intrari"
DOSAR_BACKUP = "backup_intrari"


@aplicatie.route("/")
def index():
    cursor.execute("SELECT id, nume, prenume, idManager, companie, email FROM persoane")
    utilizatori = cursor.fetchall()
    print(utilizatori)
    return render_template("index.html", users=utilizatori)


@aplicatie.route("/access", methods=["POST"])
def adauga_acces():
    date = request.get_json()
    directie = date.get("sens")
    id_persoana = date.get("idPersoana")
    id_poarta = date.get("idPoarta")
    data = date.get("data")

    # Converteste stringul datetime ISO 8601 in format datetime MySQL
    obiect_datetime = datetime.fromisoformat(data.rstrip("Z"))
    sir_datetime_mysql = obiect_datetime.strftime("%Y-%m-%d %H:%M:%S")

    cursor = bd.cursor()
    raspuns = {}
    try:
        # Inserează noul acces în tabelă
        cursor.execute(
            "INSERT INTO acces (data, sens, id_persoana, poarta) VALUES (%s, %s, %s, %s)",
            (sir_datetime_mysql, directie, id_persoana, id_poarta),
        )
        bd.commit()
        raspuns["status"] = "succes"
        raspuns["message"] = "Acces adăugat cu succes."
    except mysql.connector.Error as err:
        print("A apărut o eroare: {}".format(err))
        raspuns["status"] = "eroare"
        raspuns["message"] = "Nu s-a putut adăuga accesul."
    finally:
        cursor.close()

    return jsonify(raspuns)


@aplicatie.route("/user", methods=["POST"])
def adauga_utilizator():
    # Preia datele din cerere
    date = request.get_json()
    nume = date.get("nume")
    prenume = date.get("prenume")
    id_manager = date.get("idManager")
    companie = date.get("companie")
    email = date.get("email")

    cursor = bd.cursor()
    raspuns = {}

    try:
        # Inserează noul utilizator în tabelă
        cursor.execute(
            "INSERT INTO persoane (nume, prenume, idManager, companie, email) VALUES (%s, %s, %s, %s, %s)",
            (nume, prenume, id_manager, companie, email),
        )
        bd.commit()
        raspuns["status"] = "succes"
        raspuns["message"] = "Utilizator adăugat cu succes."
    except mysql.connector.Error as err:
        print("A apărut o eroare: {}".format(err))
        raspuns["status"] = "eroare"
        raspuns["message"] = "Nu s-a putut adăuga utilizatorul."
    finally:
        cursor.close()

    return jsonify(raspuns)


def calculeaza_ore(dosar_supraveghere):
    cursor1 = bd.cursor(dictionary=True)
    cursor2 = bd.cursor()

    # Extrage înregistrările din baza de date
    cursor1.execute(
        """
        SELECT id_persoana, data, sens FROM acces
        ORDER BY id_persoana, data
    """
    )
    inregistrari = cursor1.fetchall()

    # Converteste înregistrările în DataFrame
    df = pd.DataFrame(inregistrari)
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])

        ore_lucrate = {}
        for id_persoana, grup in df.groupby("id_persoana"):
            timp_total = timedelta()
            timp_intrare = None
            for _, rand in grup.iterrows():
                if rand["sens"] == "in":
                    timp_intrare = rand["data"]
                elif rand["sens"] == "out" and timp_intrare is not None:
                    timp_total += rand["data"] - timp_intrare
                    timp_intrare = None
            ore = timp_total.total_seconds() / 3600
            ore_lucrate[id_persoana] = ore

        # Pregătește căile fișierelor
        astazi_str = datetime.now().strftime("%Y%m%d")
        cale_fisier_csv = os.path.join(
            dosar_supraveghere, f"{astazi_str}_chiulangii.csv"
        )
        cale_fisier_txt = os.path.join(
            dosar_supraveghere, f"{astazi_str}_chiulangii.txt"
        )

        # Deschide fișierele pentru scriere
        with open(cale_fisier_csv, mode="w", newline="") as fisier_csv, open(
            cale_fisier_txt, "w"
        ) as fisier_txt:
            scriitor_csv = csv.writer(fisier_csv)
            scriitor_csv.writerow(["Nume", "OreLucrate"])  # Scrie antetul CSV

            for id_persoana, ore in ore_lucrate.items():
                if ore < 8:
                    cursor2.execute(
                        "SELECT nume, email FROM persoane WHERE id = %s", (id_persoana,)
                    )
                    rezultat = cursor2.fetchone()
                    nume = rezultat[0] if rezultat else "Necunoscut"
                    scriitor_csv.writerow([nume, ore])
                    fisier_txt.write(f"{nume}, {ore}\n")

    cursor1.close()
    cursor2.close()
    bd.close()


def supravegheaza_dosar():
    fisiere_cunoscute = set(os.listdir(DOSAR_SUPRAVEGHERE))
    while True:
        time.sleep(5)  # Așteaptă 5 secunde
        fisiere_curente = set(os.listdir(DOSAR_SUPRAVEGHERE))
        fisiere_noi = fisiere_curente - fisiere_cunoscute
        if fisiere_noi:
            print(f"Fisiere noi detectate: {fisiere_noi}")
            for fisier_nou in fisiere_noi:
                radacina, extensie = os.path.splitext(fisier_nou)
                if extensie == ".csv":
                    procesator_csv = ProcesorFisierCsv(DOSAR_SUPRAVEGHERE, DOSAR_BACKUP)
                    procesator_csv.proceseaza_fisier(fisier_nou)
                if extensie == ".txt":
                    procesator_txt = ProcesorFisierTxt(DOSAR_SUPRAVEGHERE, DOSAR_BACKUP)
                    procesator_txt.proceseaza_fisier(fisier_nou)

        fisiere_cunoscute = fisiere_curente
        print(f"Fisiere: {fisiere_cunoscute}")


if __name__ == "__main__":
    # Porneste task-ul de supraveghere a dosarului într-un fir separat
    fir = Thread(target=supravegheaza_dosar)
    fir.daemon = True  # Daemonizează firul
    fir.start()

    programator = BackgroundScheduler()
    programator.add_job(
        lambda: calculeaza_ore(dosar_supraveghere=DOSAR_BACKUP), "cron", hour=20
    )
    programator.start()
    calculeaza_ore(dosar_supraveghere=DOSAR_BACKUP)
    aplicatie.run(debug=True)
