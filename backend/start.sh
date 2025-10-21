#!/bin/bash
cd /home/rob/Documentos/ProyectosPython/Rechnungen/Rechnungen-GoBD-DE/backend
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
