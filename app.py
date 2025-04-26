from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
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
app.secret_key = 'clave_secreta_segura'  # Cambia esto por una clave segura

# Credenciales de usuario
USUARIO = "Kubis"
CONTRASEÑA = "GustavoKubis"

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == USUARIO and password == CONTRASEÑA:
        session["logged_in"] = True
        return redirect(url_for("menu"))
    else:
        return "❌ Usuario o contraseña incorrectos", 401

@app.route("/menu")
def menu():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("menu.html")

@app.route("/login-page")
def login_page():
    return render_template("menu.html")  # Usa el mismo archivo para el formulario de inicio de sesión

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login_page"))

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
    data = request.get_json()
    desde = data.get("desde")
    hasta = data.get("hasta")

    try:
        # Reemplazamos por tu IP real y puerto de la API local
        response = requests.get(
            "http://170.82.145.121:5000/api/cdc",
            params={"desde": desde, "hasta": hasta},
            timeout=10
        )
        result = response.json()

        if result.get("ok"):
            cdcs = [r["cdc"] for r in result["resultados"]]
            return jsonify({"cdcs": cdcs})
        else:
            return jsonify({"error": result.get("error", "Error desconocido")}), 500

    except Exception as e:
        return jsonify({"error": f"No se pudo contactar con la API Firebird: {e}"}), 500

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