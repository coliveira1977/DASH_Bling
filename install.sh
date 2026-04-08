#!/bin/bash
# =============================================================================
# DASH_Bling - Script de Instalacao Automatica
# Bling x Mercado Livre Sync Dashboard
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

echo ""
echo "============================================="
echo "  DASH_Bling - Instalacao Automatica"
echo "  Bling x Mercado Livre Sync Dashboard"
echo "============================================="
echo ""

# --- Verificar Python ---
PYTHON=""
for cmd in python3.11 python3.10 python3.9 python3; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    error "Python 3.9+ nao encontrado. Instale antes de continuar."
fi

PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
log "Python encontrado: $PYTHON ($PY_VERSION)"

# --- Diretorio de instalacao ---
INSTALL_DIR="${1:-$(pwd)}"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
fi
log "Diretorio de instalacao: $INSTALL_DIR"

# --- Criar virtualenv ---
if [ ! -d "$INSTALL_DIR/venv" ]; then
    log "Criando ambiente virtual..."
    $PYTHON -m venv "$INSTALL_DIR/venv"
else
    warn "Ambiente virtual ja existe, reutilizando."
fi

source "$INSTALL_DIR/venv/bin/activate"
log "Ambiente virtual ativado."

# --- Instalar dependencias ---
log "Instalando dependencias..."
pip install --upgrade pip -q
pip install -r "$INSTALL_DIR/requirements.txt" -q
log "Dependencias instaladas com sucesso."

# --- Configurar .env ---
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        chmod 600 "$INSTALL_DIR/.env"
        warn "Arquivo .env criado a partir do .env.example."
        warn "EDITE o .env com suas credenciais antes de iniciar!"
    else
        error "Arquivo .env.example nao encontrado."
    fi
else
    log "Arquivo .env ja existe."
fi

# --- Verificar permissoes ---
chmod 600 "$INSTALL_DIR/.env" 2>/dev/null || true
if [ -f "$INSTALL_DIR/bling_tokens.json" ]; then
    chmod 600 "$INSTALL_DIR/bling_tokens.json"
fi
log "Permissoes de arquivos sensiveis configuradas (600)."

# --- Testar importacao ---
log "Verificando instalacao..."
$PYTHON -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from app.main import app
print('FastAPI app carregado com sucesso.')
" || error "Falha ao carregar a aplicacao."

log "Instalacao concluida com sucesso!"

echo ""
echo "============================================="
echo "  Proximos passos:"
echo "============================================="
echo ""
echo "  1. Edite o arquivo .env com suas credenciais:"
echo "     nano $INSTALL_DIR/.env"
echo ""
echo "  2. Inicie o servidor:"
echo "     cd $INSTALL_DIR"
echo "     source venv/bin/activate"
echo "     uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  3. Acesse: http://localhost:8000"
echo ""
echo "  4. Autorize o Bling: http://localhost:8000/bling/auth"
echo ""
echo "============================================="
