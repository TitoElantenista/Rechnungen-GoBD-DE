#!/bin/bash

# Script para iniciar Backend y Frontend simultáneamente

echo "🚀 Iniciando Rechnungsgenerator GoBD..."
echo ""

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Iniciar Backend en segundo plano
echo "📦 Iniciando Backend (FastAPI)..."
cd "$BASE_DIR/backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend corriendo en http://localhost:8000 (PID: $BACKEND_PID)"
echo "   📚 API Docs: http://localhost:8000/docs"

# Esperar 3 segundos para que backend inicie
sleep 3

# Iniciar Frontend en segundo plano
echo ""
echo "🎨 Iniciando Frontend (React + Vite)..."
cd "$BASE_DIR/frontend"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend corriendo en http://localhost:5173 (PID: $FRONTEND_PID)"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Aplicación iniciada correctamente!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Abrir en navegador:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000/docs"
echo ""
echo "🔐 Credenciales:"
echo "   Usuario:  admin"
echo "   Password: admin"
echo ""
echo "📊 Ver logs:"
echo "   Backend:  tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 Para detener:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   o ejecuta: ./stop_all.sh"
echo ""
echo "════════════════════════════════════════════════════════════"

# Guardar PIDs para poder detener después
echo "$BACKEND_PID" > /tmp/rechnungen_backend.pid
echo "$FRONTEND_PID" > /tmp/rechnungen_frontend.pid

# Mantener script corriendo
wait
