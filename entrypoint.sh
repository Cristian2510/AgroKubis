#!/bin/bash
apt-get update && apt-get install -y firebird-dev
gunicorn app:app --bind 0.0.0.0:8080
