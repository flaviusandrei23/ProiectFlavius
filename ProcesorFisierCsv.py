import os
import pandas as pd
from datetime import datetime
from shutil import move
import mysql.connector
from ProcesorFisier import ProcesorFisier

class ProcesorFisierCsv(ProcesorFisier):
    def proceseaza_fisier(self, nume_fisier):
        cale_completa = os.path.join(self.dosar_supraveghere, nume_fisier)
        df = pd.read_csv(cale_completa)
        self._proceseaza_dataframe(df, nume_fisier)
        self.muta_in_backup(nume_fisier)

    def _proceseaza_dataframe(self, df, nume_fisier):
        bd = mysql.connector.connect(**self.config_bd)
        cursor = bd.cursor()
        for _, rand in df.iterrows():
            try:
                obiect_datetime = datetime.fromisoformat(rand['Data'].rstrip('Z'))
                sir_datetime_mysql = obiect_datetime.strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO acces (id_persoana, data, sens, poarta) VALUES (%s, %s, %s, %s)",
                    (rand['IdPersoana'], sir_datetime_mysql, rand['Sens'], self.iaIdPoarta(numeFisier=nume_fisier))
                )
                bd.commit()
            except mysql.connector.Error as err:
                print(f"A eșuat inserarea în baza de date: {err}")
                bd.rollback()
        cursor.close()
        bd.close()
