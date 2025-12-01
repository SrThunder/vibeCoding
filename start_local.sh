#!/bin/bash
# Script para iniciar Backend + Frontend + Testing en localhost
# Uso: ./start_local.sh

set -e

PROJECT_DIR="/Users/jorgec/vibeCoding"
VENV_PATH="$PROJECT_DIR/.venv/bin/activate"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DOLMEN RAG MVP - LOCAL LAUNCHER       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Verificar que estamos en el directorio correcto
cd "$PROJECT_DIR"

# Verificar .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ ERROR: No se encuentra .env${NC}"
    echo "Por favor copia backend/.env.example a .env y completa las credenciales"
    exit 1
fi

echo -e "${GREEN}✅ Directorio correcto: $PROJECT_DIR${NC}"
echo -e "${GREEN}✅ Archivo .env encontrado${NC}\n"

# Activar venv
source "$VENV_PATH"
echo -e "${GREEN}✅ Virtual environment activado${NC}\n"

# Función para limpiar procesos al salir
cleanup() {
    echo -e "\n${YELLOW}⏹️  Deteniendo servicios...${NC}"
    pkill -f "uvicorn backend.main:app" || true
    pkill -f "streamlit run" || true
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

trap cleanup EXIT INT TERM

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}INICIANDO SERVICIOS...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Matar procesos anteriores si existen
pkill -f "uvicorn backend.main:app" || true
pkill -f "streamlit run" || true
sleep 1

# Iniciar Backend
echo -e "${YELLOW}🚀 Iniciando Backend FastAPI en puerto 8000...${NC}"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}   PID: $BACKEND_PID${NC}"

# Esperar a que backend esté listo
echo "   Esperando a que backend esté listo..."
sleep 3

# Verificar que backend está corriendo
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend no respondió en http://localhost:8000${NC}"
    echo "   Ver logs: tail -f /tmp/backend.log"
    exit 1
fi
echo -e "${GREEN}   ✅ Backend respondiendo${NC}\n"

# Iniciar Frontend
echo -e "${YELLOW}🚀 Iniciando Frontend Streamlit en puerto 8501...${NC}"
streamlit run frontend/app.py --logger.level=info --client.toolbarPosition=top > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}   PID: $FRONTEND_PID${NC}"

# Esperar a que frontend esté listo
echo "   Esperando a que frontend esté listo..."
sleep 5

# Verificar que frontend está corriendo
if ! curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Frontend puede estar iniciando, espera unos segundos...${NC}"
fi
echo -e "${GREEN}   ✅ Frontend iniciando${NC}\n"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ SERVICIOS ACTIVOS ✨${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "📍 Backend:       ${GREEN}http://localhost:8000${NC}"
echo -e "   Docs:         ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   Health:       ${GREEN}http://localhost:8000/health${NC}\n"

echo -e "📍 Frontend:      ${GREEN}http://localhost:8501${NC}\n"

echo -e "${YELLOW}📊 Ejecutar Tests (en otra terminal):${NC}"
echo -e "   ${GREEN}python scripts/test_local.py${NC}\n"

echo -e "${YELLOW}📋 Ver Logs:${NC}"
echo -e "   Backend:  ${GREEN}tail -f /tmp/backend.log${NC}"
echo -e "   Frontend: ${GREEN}tail -f /tmp/frontend.log${NC}\n"

echo -e "${YELLOW}🛑 Para detener: Presiona Ctrl+C${NC}\n"

# Mantener el script corriendo
while true; do
    sleep 1
done
