import fdb

# Configuración de la base de datos (servidor público)
dsn = '170.82.145.121/3050:C:/Sistema Gol/Database/DATABASE.FDB'
user = 'SYSDBA'
password = 'di20071987'
charset = 'NONE'

def obtener_cdcs_por_fecha(desde, hasta):
    # ❌ Elimina fdb.load_api, no funciona en Render
    # fdb.load_api(fb_library_name)

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
