#!/bin/bash
# Este archivo se ejecuta al iniciar la app en Render

# Ejecutar gunicorn para correr la app
gunicorn app:app --bind 0.0.0.0:8080
