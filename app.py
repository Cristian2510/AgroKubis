from flask import Flask, render_template, request, jsonify, send_file
import requests
import config
import pandas as pd
from datetime import datetime
from conexion import obtener_cdcs_por_fecha
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

# ✅ NUEVA RUTA PARA PROBAR CONEXIÓN
@app.route("/test-conexion")
def test_conexion():
    from datetime import datetime
    try:
        from conexion import obtener_cdcs_por_fecha
        hoy = datetime.today().strftime('%Y-%m-%d')
        obtener_cdcs_por_fecha(hoy, hoy)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# Menú y vistas
@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/index")
def vista_index():
    return render_template("index.html")

@app.route("/consulta-set")
def vista_consulta_set():
    return render_template("consultaSet.html")

@app.route("/")
def redireccion_a_menu():
    return render_template("menu.html")

# Consulta CDC sin guardar archivos
@app.route("/consultar", methods=["POST"])
def consultar():
    data = request.json
    raw_list = data.get("cdcList", [])
    cdcList = [{"cdc": c.strip()} for c in raw_list if c.strip()]

    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }

    url = f"https://api.facturasend.com.py/{config.TENANT_ID}/de/estado"
    try:
        response = requests.post(url, json={"cdcList": cdcList}, headers=headers)
        data_respuesta = response.json()

        if not data_respuesta.get("success", True) or "Invalid token" in data_respuesta.get("error", ""):
            return jsonify({
                "error": "❌ Token inválido o expirado.",
                "mensaje": "Verifica que tu API_KEY comience con 'api_key_' y sea válida.",
                "respuesta": data_respuesta
            }), 401

        app.config['RESPUESTA_CDC'] = data_respuesta
        return jsonify(data_respuesta)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "detalle": "No se pudo contactar con la API"
        }), 500

# Informe en formato JSON
@app.route("/informe", methods=["GET"])
def informe():
    datos = app.config.get('RESPUESTA_CDC')
    if not datos:
        return jsonify({"error": "No hay respuesta disponible. Realiza una consulta primero."}), 404

    lista = datos.get("deList", [])
    df = pd.DataFrame(lista)
    df["nro_factura"] = df["numero"].str.extract(r"(\d+)$").astype(int)
    df = df.sort_values(by="nro_factura")

    todos = set(range(df["nro_factura"].min(), df["nro_factura"].max() + 1))
    presentes = set(df["nro_factura"])
    faltantes = sorted(todos - presentes)

    df["Fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    df["Factura"] = df["numero"]
    df["Resp"] = df["respuesta_mensaje"]
    df["CDC"] = df["cdc"]
    informe_df = df[["Fecha", "Factura", "Resp", "CDC"]]

    for falta in faltantes:
        informe_df = pd.concat([informe_df, pd.DataFrame([{
            "Fecha": "—",
            "Factura": f"001-001-{str(falta).zfill(7)} (❌ Faltante)",
            "Resp": "—",
            "CDC": "—"
        }])], ignore_index=True)

    return jsonify(informe_df.to_dict(orient="records"))

# Búsqueda por fecha en base de datos
@app.route("/buscar_cdcs", methods=["POST"])
def buscar_cdcs():
    data = request.json
    desde = data.get("desde")
    hasta = data.get("hasta")

    try:
        registros = obtener_cdcs_por_fecha(desde, hasta)
        cdcList = [fila[2] for fila in registros]
        return jsonify({"cdcs": cdcList})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Exportar a Excel
@app.route("/informe/excel", methods=["GET"])
def descargar_excel():
    datos = app.config.get('RESPUESTA_CDC')
    if not datos:
        return jsonify({"error": "No hay datos para exportar"}), 404

    lista = datos.get("deList", [])
    df = pd.DataFrame(lista)
    df["nro_factura"] = df["numero"].str.extract(r"(\d+)$").astype(int)
    df = df.sort_values(by="nro_factura")

    todos = set(range(df["nro_factura"].min(), df["nro_factura"].max() + 1))
    presentes = set(df["nro_factura"])
    faltantes = sorted(todos - presentes)

    df["Fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    df["Factura"] = df["numero"]
    df["Resp"] = df["respuesta_mensaje"]
    df["CDC"] = df["cdc"]
    informe = df[["Fecha", "Factura", "Resp", "CDC"]]

    for falta in faltantes:
        informe = pd.concat([informe, pd.DataFrame([{
            "Fecha": "—",
            "Factura": f"001-001-{str(falta).zfill(7)} (❌ Faltante)",
            "Resp": "—",
            "CDC": "—"
        }])], ignore_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        informe.to_excel(writer, index=False)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Informe_CDC.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Exportar a PDF
@app.route("/informe/pdf", methods=["GET"])
def descargar_pdf():
    datos = app.config.get('RESPUESTA_CDC')
    if not datos:
        return jsonify({"error": "No hay datos para exportar"}), 404

    lista = datos.get("deList", [])
    df = pd.DataFrame(lista)
    df["nro_factura"] = df["numero"].str.extract(r"(\d+)$").astype(int)
    df = df.sort_values(by="nro_factura")

    todos = set(range(df["nro_factura"].min(), df["nro_factura"].max() + 1))
    presentes = set(df["nro_factura"])
    faltantes = sorted(todos - presentes)

    df["Fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    df["Factura"] = df["numero"]
    df["Resp"] = df["respuesta_mensaje"]
    df["CDC"] = df["cdc"]
    informe = df[["Fecha", "Factura", "Resp", "CDC"]]

    for falta in faltantes:
        informe = pd.concat([informe, pd.DataFrame([{
            "Fecha": "—",
            "Factura": f"001-001-{str(falta).zfill(7)} (❌ Faltante)",
            "Resp": "—",
            "CDC": "—"
        }])], ignore_index=True)

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    estilo = getSampleStyleSheet()
    elementos = [Paragraph("📋 Informe de Facturas Validadas", estilo['Title']), Spacer(1, 12)]

    datos_tabla = [["Fecha", "Factura", "Respuesta", "CDC"]] + informe.values.tolist()
    tabla = Table(datos_tabla, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#00c853")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
    ]))

    elementos.append(tabla)
    doc.build(elementos)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="Informe_CDC.pdf", mimetype="application/pdf")

# Consulta CDC usando Selenium
@app.route("/consultar_selenium", methods=["POST"])
def consultar_selenium():
    data = request.json
    cdc_value = data.get("cdc")
    if not cdc_value:
        return jsonify({"error": "No se proporcionó un CDC válido"}), 400

    try:
        driver = webdriver.Chrome()
        driver.get("https://ekuatia.set.gov.py/consultas/")
        cdc_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='CDC']"))
        )
        cdc_input.send_keys(cdc_value)

        print("Por favor, resuelve el reCAPTCHA manualmente.")
        time.sleep(15)

        buscar_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Consultar')]"))
        )
        buscar_button.click()
        time.sleep(5)

        driver.quit()
        return jsonify({"mensaje": "Consulta realizada con éxito. Verifica los resultados en el navegador."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👇 ESTA PARTE ES PARA PRODUCCIÓN CON GUNICORN (NO USAR app.run)
#if __name__ == "__main__":
#    app.run(debug=True)
