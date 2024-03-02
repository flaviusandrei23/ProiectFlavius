import os
import pandas as pd
from datetime import datetime
from shutil import move
import mysql.connector
from ProcesorFisier import ProcesorFisier

class ProcesorFisierTxt(ProcesorFisier):
    def proceseaza_fisier(self, nume_fisier):
        cale_completa = os.path.join(self.dosar_supraveghere, nume_fisier)
        with open(cale_completa, 'r') as fisier:
            linii = fisier.readlines()
            self._proceseaza_linii(linii, nume_fisier)
        self.muta_in_backup(nume_fisier)

    def _proceseaza_linii(self, linii, nume_fisier):
        bd = mysql.connector.connect(**self.config_bd)
        cursor = bd.cursor()
        for linie in linii:
            id_persoana, data, sens = linie.strip().split(',')
            try:
                obiect_datetime = datetime.fromisoformat(data.rstrip('Z'))
                sir_datetime_mysql = obiect_datetime.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO acces (id_persoana, data, sens, poarta) VALUES (%s, %s, %s, %s)",
                    (id_persoana, sir_datetime_mysql, sens.rstrip(';'), self.iaIdPoarta(numeFisier=nume_fisier))
                )
                bd.commit()
            except mysql.connector.Error as eroare:
                print(f"A eșuat inserarea în baza de date: {eroare}")
                bd.rollback()
        cursor.close()
        bd.close()
