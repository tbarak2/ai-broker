#!/usr/bin/env bash
# deploy.sh — Build, start, and migrate the AI Broker stack
set -euo pipefail

COMPOSE="docker compose"
BACKEND="ai_broker-backend-1"

# ── Colours ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[deploy]${NC} $*"; }
warning() { echo -e "${YELLOW}[deploy]${NC} $*"; }
error()   { echo -e "${RED}[deploy]${NC} $*" >&2; exit 1; }

# ── Parse flags ────────────────────────────────────────────────────────────────
BUILD=false
DOWN=false

for arg in "$@"; do
  case $arg in
    --build|-b)  BUILD=true ;;
    --down|-d)   DOWN=true ;;
    --help|-h)
      echo "Usage: ./deploy.sh [--build] [--down]"
      echo "  --build, -b   Rebuild Docker images before starting"
      echo "  --down,  -d   Stop and remove containers first (fresh restart)"
      exit 0 ;;
    *) error "Unknown argument: $arg" ;;
  esac
done

# ── Verify .env exists ─────────────────────────────────────────────────────────
if [[ ! -f .env ]]; then
  error ".env file not found. Copy .env.example and fill in your API keys."
fi

# ── Optional: tear down first ──────────────────────────────────────────────────
if $DOWN; then
  warning "Stopping existing containers..."
  $COMPOSE down
fi

# ── Build images ───────────────────────────────────────────────────────────────
if $BUILD; then
  info "Building Docker images..."
  $COMPOSE build
fi

# ── Start the stack ────────────────────────────────────────────────────────────
info "Starting all services..."
$COMPOSE up -d

# ── Wait for backend to be healthy ─────────────────────────────────────────────
info "Waiting for backend to be ready..."
RETRIES=30
until docker exec "$BACKEND" python manage.py check --deploy 2>/dev/null | grep -q "System check" \
   || docker exec "$BACKEND" python manage.py check 2>/dev/null | grep -q "System check"; do
  RETRIES=$((RETRIES - 1))
  if [[ $RETRIES -le 0 ]]; then
    error "Backend did not become ready in time. Check logs: docker compose logs backend"
  fi
  sleep 2
done

# ── Run migrations ─────────────────────────────────────────────────────────────
info "Running database migrations..."
docker exec "$BACKEND" python manage.py migrate --noinput

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
info "Deployment complete!"
echo -e "  Frontend  → ${GREEN}http://localhost:5173${NC}"
echo -e "  API       → ${GREEN}http://localhost:8010/api/${NC}"
echo ""
info "Useful commands:"
echo "  docker compose logs -f backend    # backend logs"
echo "  docker compose logs -f celery     # celery logs"
echo "  docker compose ps                 # service status"
echo "  docker compose down               # stop everything"
