import requests

API_FIREBIRD = "http://170.82.145.121:5000/api/cdc"

def obtener_cdcs_por_fecha(desde, hasta):
    try:
        response = requests.get(API_FIREBIRD, params={"desde": desde, "hasta": hasta})
        datos = response.json()

        if datos.get("ok"):
            return [(d["fecha"], d["lanzamiento"], d["cdc"]) for d in datos["resultados"]]
        else:
            raise Exception(datos.get("error", "Error desconocido en la API local"))
    except Exception as e:
        raise Exception(f"Error consultando API Firebird: {e}")
