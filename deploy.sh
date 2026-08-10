#!/usr/bin/env bash

# ==============================================================================
# Tianaluxora Website Backend Deployment Script
# Target Server Location: /var/www/tianaluxora-website-be
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BE_DIR="${BE_DIR:-/var/www/tianaluxora-website-be}"
BRANCH="${BRANCH:-main}"

echo -e "${CYAN}========================================================================${NC}"
echo -e "${CYAN}            Deploying Tianaluxora Website Backend                      ${NC}"
echo -e "${CYAN}========================================================================${NC}"

if [ -d "$BE_DIR" ]; then
  cd "$BE_DIR"
fi

echo -e "${YELLOW}➜ Pulling latest backend code (origin/${BRANCH})...${NC}"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [ -d "venv" ]; then
  echo -e "${YELLOW}➜ Updating python virtualenv dependencies...${NC}"
  source venv/bin/activate
  if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
  fi
fi

echo -e "${YELLOW}➜ Restarting systemd service 'tianaluxora-website-be'...${NC}"
sudo systemctl restart tianaluxora-website-be

echo -e "${GREEN}✓ Backend deployment successful!${NC}"
