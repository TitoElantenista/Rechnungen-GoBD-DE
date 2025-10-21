#!/bin/bash

echo "🛑 Deteniendo Rechnungsgenerator GoBD..."

# Leer PIDs
if [ -f /tmp/rechnungen_backend.pid ]; then
    BACKEND_PID=$(cat /tmp/rechnungen_backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "   Deteniendo Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "   ✅ Backend detenido"
    fi
    rm /tmp/rechnungen_backend.pid
fi

if [ -f /tmp/rechnungen_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/rechnungen_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "   Deteniendo Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "   ✅ Frontend detenido"
    fi
    rm /tmp/rechnungen_frontend.pid
fi

echo ""
echo "✅ Todos los servicios detenidos"
