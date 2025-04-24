import fdb
import os
import platform

# Configuración de la base de datos
dsn = '170.82.145.121/3050:C:/Sistema Gol/Database/DATABASE.FDB'
user = 'SYSDBA'
password = 'di20071987'
charset = 'NONE'

# Solo cargar la DLL en Windows
if platform.system() == 'Windows':
    fb_library_name = r'C:\Program Files\Firebird\Firebird_3_0\bin\fbclient.dll'
    fdb.load_api(fb_library_name)

def obtener_cdcs_por_fecha(desde, hasta):
    con = fdb.connect(
        dsn=dsn,
        user=user,
        password=password,
        charset=charset
    )

    cur = con.cursor()

    query = """
        SELECT DATA, LANCAMENTO, CDC
        FROM faturas_crecon
        WHERE ESTADO_SET = '3'
        AND DATA BETWEEN ? AND ?
    """

    cur.execute(query, (desde, hasta))
    resultados = cur.fetchall()

    con.close()
    return resultados
