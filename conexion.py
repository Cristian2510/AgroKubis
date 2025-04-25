import fdb
import platform

dsn = '170.82.145.121/3050:C:/Sistema Gol/Database/DATABASE.FDB'
user = 'SYSDBA'
password = 'di20071987'
charset = 'NONE'

# Detectar entorno para cargar la librería si estás en Windows
if platform.system() == 'Windows':
    fdb.load_api('C:/Program Files/Firebird/Firebird_3_0/bin/fbclient.dll')
# No cargar librería en Linux (Railway lo usará por defecto si está instalada)

def obtener_cdcs_por_fecha(desde, hasta):
    con = fdb.connect(
        dsn=dsn,
        user=user,
        password=password,
        charset=charset
    )
    cur = con.cursor()
    cur.execute("""
        SELECT DATA, LANCAMENTO, CDC
        FROM faturas_crecon
        WHERE ESTADO_SET = '3'
        AND DATA BETWEEN ? AND ?
    """, (desde, hasta))
    resultados = cur.fetchall()
    con.close()
    return resultados
