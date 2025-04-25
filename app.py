from flask import Flask, render_template, request, jsonify, send_file
import requests
import config
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
import time

app = Flask(__name__)

# ✅ RUTA DE TEST DE CONEXIÓN A API EXTERNA
@app.route("/test-conexion")
def test_conexion():
    try:
        url = "http://170.82.145.121:5000/api/cdc?desde=2025-01-01&hasta=2025-01-02"
        res = requests.get(url)
        data = res.json()
        if not data.get("ok"):
            return jsonify({"ok": False, "error": data.get("error")})
        return jsonify({"ok": True, "cantidad": len(data.get("resultados", []))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# 🧾 MENÚ Y VISTAS
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

# 📡 CONSULTA CDC
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

# 🔍 CONSULTA POR FECHA USANDO API EXTERNA
@app.route("/buscar_cdcs", methods=["POST"])
def buscar_cdcs():
    data = request.json
    desde = data.get("desde")
    hasta = data.get("hasta")

    try:
        url = f"http://170.82.145.121:5000/api/cdc?desde={desde}&hasta={hasta}"
        response = requests.get(url)
        json_data = response.json()

        if not json_data.get("ok"):
            return jsonify({"error": json_data.get("error")}), 500

        cdc_list = [fila["cdc"] for fila in json_data.get("resultados", [])]
        return jsonify({"cdcs": cdc_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📦 EXPORTACIÓN JSON
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

# 👇 ESTA PARTE ES PARA PRODUCCIÓN CON GUNICORN (NO USAR app.run)
# if __name__ == "__main__":
#     app.run(debug=True)