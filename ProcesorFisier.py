import os
import pandas as pd
from datetime import datetime
from shutil import move
import mysql.connector

class ProcesorFisier:
    def __init__(self, dosar_supraveghere, dosar_backup):
        self.dosar_supraveghere = dosar_supraveghere
        self.dosar_backup = dosar_backup
        self.config_bd = {
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
            'database': 'angajati'
        }

    def iaIdPoarta(self, numeFisier: str):
        # Găsește poziția ultimului punct
        pozitia_ultimului_punct = numeFisier.rfind('.')
        # Obține caracterul înainte de ultimul punct
        if pozitia_ultimului_punct != -1:  # Asigură-te că s-a găsit un punct
            caracter_inainte_ultimul_punct = numeFisier[pozitia_ultimului_punct - 1]
            return caracter_inainte_ultimul_punct
        else:
            print("Nu s-a găsit niciun punct în șir.")

    def proceseaza_fisier(self, nume_fisier):
        raise NotImplementedError("Subclasa trebuie să implementeze metoda abstractă")

    def muta_in_backup(self, nume_fisier_original):
        marca_temporala = datetime.now().strftime("%Y%m%d%H%M%S")
        nume_fisier_nou = f"{nume_fisier_original}_{marca_temporala}"
        destinatie = os.path.join(self.dosar_backup, nume_fisier_nou)
        move(os.path.join(self.dosar_supraveghere, nume_fisier_original), destinatie)
        print(f"S-a mutat {nume_fisier_original} în backup")
