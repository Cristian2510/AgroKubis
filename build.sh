#!/bin/bash
# Este archivo se ejecuta durante el build en Render

# Actualizar paquetes e instalar Firebird client
apt-get update && apt-get install -y firebird-dev firebird3.0-utils

# Instalar las dependencias del proyecto
pip install -r requirements.txt
